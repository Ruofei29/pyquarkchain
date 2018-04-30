from quarkchain.cluster.core import RootBlock, MinorBlockHeader
from quarkchain.cluster.genesis import create_genesis_minor_block, create_genesis_root_block
from quarkchain.config import NetworkId
from quarkchain.core import calculate_merkle_root, Serializable, PreprendedSizeListSerializer
from quarkchain.utils import check


class LastMinorBlockHeaderList(Serializable):
    FIELDS = [
        ("headerList", PreprendedSizeListSerializer(4, MinorBlockHeader))
    ]

    def __init__(self, headerList):
        self.headerList = headerList


class RootDb:
    """ Storage for all validated root blocks and minor blocks
    """

    def __init__(self, db):
        self.db = db
        # TODO: iterate db to recover pools or set
        # TODO: May store locally to save memory space (e.g., with LRU cache)
        self.mHashSet = set()
        self.rHeaderPool = dict()

    # ------------------------- Root block db operations --------------------------------
    def putRootBlock(self, rootBlock, lastMinorBlockHeaderList, rootBlockHash=None):
        if rootBlockHash is None:
            rootBlockHash = rootBlock.header.getHash()

        lastList = LastMinorBlockHeaderList(headerList=lastMinorBlockHeaderList)
        self.db.put(b"rblock_" + rootBlockHash, rootBlock.serialize())
        self.db.put(b"lastlist_" + rootBlockHash, lastList.serialize())
        self.rHeaderPool[rootBlockHash] = rootBlock.header

    def getRootBlockByHash(self, h):
        return RootBlock.deserialize(self.db.get(b"rblock_" + h))

    def getRootBlockHeaderByHash(self, h):
        return self.rHeaderPool.get(h)

    def getRootBlockLastMinorBlockHeaderList(self, h):
        return LastMinorBlockHeaderList.deserialize(self.db.get(b"lastlist_" + h)).headerList

    def containRootBlockByHash(self, h):
        return h in self.rHeaderPool

    # ------------------------- Minor block db operations --------------------------------
    def containMinorBlockByHash(self, h):
        return h in self.mHashSet

    def putMinorBlockHash(self, mHash):
        self.db.put(b"mheader_" + mHash, b'')
        self.mHashSet.add(mHash)

    # ------------------------- Common operations -----------------------------------------
    def put(self, key, value):
        self.db.put(key, value)

    def get(self, key, default=None):
        return self.db.get(key, default)

    def __getitem__(self, key):
        return self[key]


class RootState:
    """ State of root
    """
    def __init__(self, env, createGenesis=False, db=None):
        self.env = env
        self.diffCalc = self.env.config.ROOT_DIFF_CALCULATOR
        self.diffHashFunc = self.env.config.DIFF_HASH_FUNC
        self.rawDb = db if db is not None else env.db
        self.db = RootDb(self.rawDb)

        check(createGenesis)
        if createGenesis:
            self.__createGenesisBlocks()

    def __createGenesisBlocks(self):
        genesisRootBlock = create_genesis_root_block(self.env)
        genesisMinorBlockHeaderList = []
        for shardId in range(self.env.config.SHARD_SIZE):
            genesisMinorBlockHeaderList.append(
                create_genesis_minor_block(
                    env=self.env,
                    shardId=shardId,
                    hashRootBlock=genesisRootBlock.header.getHash()).header)
        self.db.putRootBlock(genesisRootBlock, genesisMinorBlockHeaderList)
        self.tip = genesisRootBlock.header

    def addValidatedMinorBlockHash(self, h):
        self.db.putMinorBlockHash(h)

    def addBlock(self, block):
        """ Add new block.
        return True if a longest block is added, False otherwise
        There are a couple of optimizations can be done here:
        - the root block could only contain minor block header hashes as long as the shards fully validate the headers
        - the header (or hashes) are un-ordered as long as they contains valid sub-chains from previous root block
        """

        if not self.db.containRootBlockByHash(block.header.hashPrevBlock):
            raise ValueError("previous hash block mismatch")
        prevLastMinorBlockHeaderList = self.db.getRootBlockLastMinorBlockHeaderList(block.header.hashPrevBlock)
        prevBlockHeader = self.db.getRootBlockHeaderByHash(block.header.hashPrevBlock)

        if block.header.createTime <= prevBlockHeader.createTime:
            raise ValueError("incorrect create time tip time {}, new block time {}".format(
                block.header.createTime, prevBlockHeader.createTime))

        blockHash = block.header.getHash()

        # Check the merkle tree
        merkleHash = calculate_merkle_root(block.minorBlockHeaderList)
        if merkleHash != block.header.hashMerkleRoot:
            raise ValueError("incorrect merkle root")

        # Check difficulty
        if not self.env.config.SKIP_ROOT_DIFFICULTY_CHECK:
            if self.env.config.NETWORK_ID == NetworkId.MAINNET:
                diff = self.getNextBlockDifficulty(block.header.createTime)
                metric = diff * int.from_bytes(blockHash, byteorder="big")
                if metric >= 2 ** 256:
                    raise ValueError("insufficient difficulty")
            elif block.header.coinbaseAddress.recipient != self.env.config.TESTNET_MASTER_ACCOUNT.recipient:
                raise ValueError("incorrect master to create the block")

        # Check whether all minor blocks are ordered, validated (and linked to previous block)
        shardId = 0
        prevHeader = prevLastMinorBlockHeaderList[0]
        lastMinorBlockHeaderList = []
        blockCountInShard = 0
        for idx, mHeader in enumerate(block.minorBlockHeaderList):
            if mHeader.branch.getShardId() != shardId:
                if mHeader.branch.getShardId() != shardId + 1:
                    raise ValueError("shard id must be ordered")
                if blockCountInShard < self.env.config.PROOF_OF_PROGRESS_BLOCKS:
                    raise ValueError("fail to prove progress")
                if mHeader.createTime > block.header.createTime:
                    raise ValueError("minor block create time is too large")

                lastMinorBlockHeaderList.append(block.minorBlockHeaderList[idx - 1])
                shardId += 1
                blockCountInShard = 0
                prevHeader = prevLastMinorBlockHeaderList[shardId]

            if not self.db.containMinorBlockByHash(mHeader.getHash()):
                raise ValueError("minor block is not validated")

            if mHeader.hashPrevMinorBlock != prevHeader.getHash():
                raise ValueError("minor block doesn't link to previous minor block")
            blockCountInShard += 1
            prevHeader = mHeader
            # TODO: Add coinbase

        if shardId != block.header.shardInfo.getShardSize() - 1 and self.env.config.PROOF_OF_PROGRESS_BLOCKS != 0:
            raise ValueError("fail to prove progress")
        if blockCountInShard < self.env.config.PROOF_OF_PROGRESS_BLOCKS:
            raise ValueError("fail to prove progress")

        lastMinorBlockHeaderList.append(mHeader)
        self.db.putRootBlock(block, lastMinorBlockHeaderList, rootBlockHash=blockHash)

        if self.tip.height < block.header.height:
            self.tip = block.header
            return True
        return False