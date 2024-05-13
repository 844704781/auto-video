from playhouse.pool import PooledSqliteDatabase

import os

_current_dir = os.path.dirname(__file__)
_project_root = os.path.abspath(os.path.join(_current_dir, ".."))

# 配置数据库连接池
database = PooledSqliteDatabase(_project_root + '/task.db', max_connections=500, check_same_thread=False)
