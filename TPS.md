### TPS Competition Questionnaire

*Please replace the square brackets and the text in it with your answers*

**Number of CPUs**

96

**Memory (GB)**

384 GiB

**Storage (GB)**

4 x 900 NVMe SSD

**Network**

1 Gbps LAN

**Machine Type (Optional)**

[If you are using public cloud service, note down the name of the provider and the machine type. For example, AWS EC2 m5.2xlarge.]

**Command Lines for Running Cluster**
```
pypy3 cluster.py --num_shards=512 --num_slaves=64 --root_block_interval_sec=60 --minor_block_interval_sec=10 --mine
```

**Peak TPS**

13293.28

**Video URL**

https://youtu.be/g8l_TbWNwGw

**Output From `stats` Tool**
```
----------------------------------------------------------------------------------------------------
                                      QuarkChain Cluster Stats
----------------------------------------------------------------------------------------------------
CPU:                96
Memory:             369 GB
IP:                 localhost
Shards:             512
Servers:            64
Shard Interval:     10
Root Interval:      60
Syncing:            False
Mining:             True
Peers:              172.31.44.238:38291, 172.31.45.57:38291
----------------------------------------------------------------------------------------------------
Timestamp                     TPS   Pending tx  Confirmed tx       BPS      SBPS      ROOT       CPU
----------------------------------------------------------------------------------------------------
2018-10-23 22:47:44          0.00         1800             0     57.83      0.00         1     67.79
2018-10-23 22:47:54          0.00         3000             0     57.82      0.00         1     63.85
2018-10-23 22:48:04          0.00         9600             0     57.87      0.00         1     63.42
2018-10-23 22:48:14       2215.20       244952        132912     51.48      0.00         1     59.88
2018-10-23 22:48:24       4127.50       469406        247650     45.15      0.00         1     66.75
2018-10-23 22:48:34       4989.22       548615        299353     41.67      0.00         1     64.08
2018-10-23 22:48:45       8276.65       660817        496599     29.23      0.00         1     58.45
2018-10-23 22:48:55       9413.72       721425        564823     25.88      0.00         1     66.80
2018-10-23 22:49:05      10114.90       748762        608030     24.68      0.00         1     65.08
2018-10-23 22:49:15      12314.37       859090        803046     23.72      0.00         1     62.41
2018-10-23 22:49:25      12988.15       928495        892321     23.15      0.00         1     66.94
2018-10-23 22:49:35      13293.28       966031        977089     23.43      0.00         1     64.34
```

**Additional Comment**

[If you have special setup, e.g., running a single cluster over multiple machines, the above questionnaire might not fit. Note down
whatever you want us to know here to help evaluate the result.]
