import sys

from loguru import logger

folder_ = "./logs/"
rotation_ = "100 MB"
retention_ = "30 days"
encoding_ = "utf-8"
backtrace_ = True
diagnose_ = True

# 格式里面添加了process和thread记录，方便查看多进程和线程程序
format_ = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> ' \
          '| <magenta>{process}</magenta>:<yellow>{thread}</yellow> ' \
          '| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<yellow>{line}</yellow> - <level>{message}</level>'

# 这里面采用了层次式的日志记录方式，就是低级日志文件会记录比他高的所有级别日志，这样可以做到低等级日志最丰富，高级别日志更少更关键
# debug
logger.add(folder_ + "all.log", level="DEBUG", backtrace=backtrace_, diagnose=diagnose_,
           format=format_, colorize=False,
           rotation=rotation_, retention=retention_, encoding=encoding_,
           filter=lambda record: record["level"].no >= logger.level("DEBUG").no)


logger.add(folder_ + "info.log", level="INFO", backtrace=backtrace_, diagnose=diagnose_,
           format=format_, colorize=False,
           rotation=rotation_, retention=retention_, encoding=encoding_,
           filter=lambda record: record["level"].no >= logger.level("INFO").no)

logger.add(folder_ + "error.log", level="ERROR", backtrace=backtrace_, diagnose=diagnose_,
           format=format_, colorize=False,
           rotation=rotation_, retention=retention_, encoding=encoding_,
           filter=lambda record: record["level"].no >= logger.level("ERROR").no)
