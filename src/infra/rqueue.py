import json
from infra.r import r
import time
from typing import Callable, Any
import asyncio


class RQueue():
    """
        name: 区分任务队列
        handler: 处理任务的方法
        handle_sleep: 上一个任务完成后，开始下一个任务的时间间隔
        retry_sleep: 处理失败后，重试的时间间隔
    """
    def __init__(self, name, handler: Callable[[Any], bool], handle_sleep:int = 60 * 20, retry_sleep:int = 60):
        self.name = name
        self.handler = handler
        self.handle_sleep = handle_sleep
        self.retry_sleep = retry_sleep
        self.key = self._generate_key()
        self.task_list = self._get_queue()
        self._schedule_task_processing()
        
    def _generate_key(self):
        """Generates a unique key for the queue."""
        return f"rqueue_{self.name}"
    
    def _get_queue(self):
        """Retrieves the queue from the redis."""
        queue_data = r.get(self.key)
        return json.loads(queue_data) if queue_data else []
    
    def __set_queue(self):
        """Updates the queue in the redis."""
        r.set(self.key, json.dumps( self.task_list ), ex=-1)
    
    def _schedule_task_processing(self):
        """Schedules the task processing in a separate thread or process."""
        asyncio.create_task(self._process_tasks())
        
            
    async def _process_tasks(self):
        """Processes tasks in the queue."""
        while True:
            if len(self.task_list) == 0:
                time.sleep(5)
                continue
            
            task = self.task_list[0]
            success = await self.handler(task)
            if success == True:
                self.task_list.pop(0)
                self._set_queue()
                time.sleep(self.handle_sleep)
            else: 
                time.sleep(self.retry_sleep) # retry
    
    def append(self, task: dict):
        """Appends a new task to the queue."""
        self.task_list.append(task)
        self.__set_queue()