import peewee
import datetime
from entity.task_status import Status
from common.logger_config import logger
from db.pool import database


# 定义模型类
class BaseModel(peewee.Model):
    class Meta:
        database = database


# 定义 Task 表模型
class Task(BaseModel):
    id = peewee.AutoField(primary_key=True)
    task_id = peewee.IntegerField(unique=True)
    progress = peewee.IntegerField(default=0)
    status = peewee.IntegerField(choices=[(status.value, status.name) for status in Status], default=Status.CREATED)
    status_is_sync = peewee.IntegerField(default=1)  # 状态是否与服务器同步 0:未同步 1:已同步
    message = peewee.TextField(null=True)
    err_code = peewee.IntegerField(default=0)
    server_message = peewee.TextField(null=True)
    title = peewee.TextField(null=True)
    size = peewee.TextField(null=True)
    cover = peewee.TextField(null=True)
    shots = peewee.TextField(null=True)
    video_url = peewee.TextField(null=True)
    video_path = peewee.TextField(null=True)
    create_time = peewee.IntegerField(default=int(datetime.datetime.now().timestamp()))
    update_time = peewee.IntegerField(default=int(datetime.datetime.now().timestamp()))

    def __str__(self):
        return f"Task(id={self.id}, task_id={self.task_id}, progress={self.progress}, status={self.status}, " \
               f"status_is_sync={self.status_is_sync}, title={self.title}, size={self.size}, " \
               f"shots={self.shots}, create_time={self.create_time}, update_time={self.update_time})"

# 检查模型类与数据库表结构的差异，并更新数据库表
def sync_table_structure():
    try:
        with database.atomic():
            # 检查 Task 表是否存在，不存在则创建
            if not Task.table_exists():
                Task.create_table()
                print("Table 'Task' created successfully.")

            # 检查字段是否在表中存在，不存在则添加
            fields_in_model = set(Task._meta.fields.keys())
            columns_in_table = database.get_columns('Task')

            column_names_in_table = [column.name for column in columns_in_table]

            fields_to_add = fields_in_model - set(column_names_in_table)
            for field_name in fields_to_add:
                field = Task._meta.fields[field_name]

                # 构造添加列的 SQL 语句并执行
                query = f"ALTER TABLE Task ADD COLUMN {field.name} {get_column_definition(field)}"
                database.execute_sql(query)

                print(f"Field '{field.name}' added to table 'Task'.")

            # 打印同步完成信息
            print("Table 'Task' structure synchronized successfully.")
    except peewee.OperationalError as e:
        print(f"Error occurred while synchronizing table structure: {e}")


# 获取字段的定义
def get_column_definition(field):
    if isinstance(field, peewee.CharField):
        return "VARCHAR(255)"  # 假设最大长度为 255
    elif isinstance(field, peewee.IntegerField):
        return "INTEGER"
    elif isinstance(field, peewee.TextField):
        return "TEXT"
    else:
        raise ValueError(f"Unsupported field type: {type(field)}")


class TaskMapper:

    @staticmethod
    # 检查任务是否已经存在于数据库中
    def task_exists(task_id):
        with database:
            return Task.select().where(Task.task_id == task_id).exists()

    # 批量插入任务对象（仅插入不存在于数据库中的任务）
    def bulk_insert_tasks(self, tasks):
        tasks_to_insert = []
        for task in tasks:
            if not self.task_exists(task['task_id']):
                tasks_to_insert.append(task)
        if tasks_to_insert:
            with database.atomic():
                Task.insert_many(tasks_to_insert).execute()

    # 根据id，将对应的task的status_is_sync更新成1
    @staticmethod
    def set_synced_by_task_id(task_id):
        try:
            with database.atomic():
                query = Task.update(status_is_sync=1).where(Task.task_id == task_id)
                query.execute()
        except Task.DoesNotExist:
            pass  # 如果找不到任务，则忽略异常

    @staticmethod
    def unsync_count():
        return Task.select().where((Task.status_is_sync == 0)).count()

    def get_executable_tasks(self, size):
        """
        获取可执行的任务
        优先获取刚创建的任务，其次获取失败的任务
        :param size: 要获取的任务数量
        :return: 可执行的任务列表
        """
        executable_tasks = []

        # 首先尝试获取刚创建的任务
        created_tasks = Task.select().where(Task.status == Status.CREATED).limit(size)
        executable_tasks.extend(created_tasks)

        # 计算还需要获取的任务数量
        remaining_size = size - len(executable_tasks)

        # 如果没有刚创建的任务或者任务数量不够，再获取失败的任务
        if remaining_size > 0:
            fail_tasks = Task.select().where(Task.status == Status.FAIL).limit(remaining_size)
            executable_tasks.extend(fail_tasks)

        # remaining_size = size - len(executable_tasks)
        # # 如果没有刚创建的任务或者任务数量不够，再获取失败的任务
        # if remaining_size > 0:
        #     fail_tasks = Task.select().where(Task.status == Status.DOING).limit(remaining_size)
        #     executable_tasks.extend(fail_tasks)
        return executable_tasks

    @staticmethod
    def set_status(task_id, status, message: str = None):
        """
        设置任务的状态，仅限于不是成功状态的任务
        :param message:
        :param task_id: 任务 ID
        :param status: 要设置的状态
        """
        try:
            task = Task.select().where((Task.task_id == task_id) & (Task.status != Status.SUCCESS)).first()
            if task is None:
                return
            task.status = status
            task.status_is_sync = 0
            if message is not None:
                task.message = message
            if status != Status.FAIL:
                task.message = ''
            task.save()
        except Task.DoesNotExist:
            logger.info(f"Task with ID {task_id} not found or already in SUCCESS status.")

    # 设置失败状态
    @staticmethod
    def set_fail(task_id, err_code, message: str = None):

        try:
            task = Task.select().where((Task.task_id == task_id) & (Task.status != Status.SUCCESS)).first()
            if task is None:
                return
            task.status = Status.FAIL.value
            task.err_code = err_code
            task.status_is_sync = 0
            task.message = message
            task.save()
        except Task.DoesNotExist:
            logger.info(f"Task with ID {task_id} not found or already in SUCCESS status.")

    @staticmethod
    def set_success(task_id, video_path):
        try:
            task = Task.select().where((Task.task_id == task_id) & (Task.status != Status.SUCCESS)).first()
            if task is None:
                return
            task.status = Status.SUCCESS.value
            task.status_is_sync = 0
            task.progress = 100
            task.message = 'Success'
            task.video_path = video_path
            task.save()
        except Task.DoesNotExist:
            logger.info(f"Task with ID {task_id} not found or already in SUCCESS status.")

    @staticmethod
    def set_progress(progress, task_id):
        try:
            task = Task.select().where((Task.task_id == task_id) & (Task.status != Status.SUCCESS)).first()
            if task is None:
                return
            task.progress = progress
            task.status = Status.DOING.value
            task.status_is_sync = 0
            task.save()
        except Task.DoesNotExist:
            logger.info(f"Task with ID {task_id} not found or already in SUCCESS status.")

    @staticmethod
    def update_server_message(message, task_id):
        if message is None:
            return
        try:
            task = Task.select().where((Task.task_id == task_id) & (Task.status != Status.SUCCESS)).first()
            if task is None:
                return
            task.server_message = message
            task.save()
        except Task.DoesNotExist:
            logger.info(f"Task with ID {task_id} not found or already in SUCCESS status.")

    @staticmethod
    def get(task_id):
        try:
            return Task.select().where((Task.task_id == task_id) & (Task.status != Status.SUCCESS)).first()
        except Task.DoesNotExist:
            return None

    @staticmethod
    def get_doing_tasks():
        """
        获取当前正在执行的任务列表
        :return: 当前正在执行的任务列表
        """
        return Task.select().where(Task.status == Status.DOING)

    @staticmethod
    def get_un_success_count():
        return Task.select().where((Task.status != Status.SUCCESS)).count()

    @staticmethod
    def remove(_id):
        # 计算要删除的任务数
        count = Task.delete().where((Task.status != Status.SUCCESS) & (Task.id == _id)).execute()
        return count

    @staticmethod
    def update_shots(shots, task_id):
        if shots is None:
            return
        try:
            task = Task.select().where((Task.task_id == task_id) & (Task.status != Status.SUCCESS)).first()
            if task is None:
                return
            task.shots = shots
            task.save()
        except Task.DoesNotExist:
            logger.info(f"Task with ID {task_id} not found or already in SUCCESS status.")

    @staticmethod
    def find_unsync_task():
        task = Task.select().where((Task.status_is_sync == 0)).first()
        return task


# 创建表
def create_tables():
    with database:
        database.create_tables([Task])


# 检查是否已创建表的标志
def is_table_created():
    return Task.table_exists()
