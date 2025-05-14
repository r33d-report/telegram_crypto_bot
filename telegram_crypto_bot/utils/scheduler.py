
"""
Scheduler for Crypto Trading Telegram Bot.

This module provides functionality for scheduling tasks at specified intervals,
such as running trading strategies or checking price alerts.
"""

import time
import threading
import logging
import schedule
from typing import Dict, List, Optional, Union, Any, Callable
from datetime import datetime, timedelta

from utils.logger import setup_logger

class TaskScheduler:
    """
    Scheduler for running tasks at specified intervals.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the task scheduler.
        
        Args:
            logger (Optional[logging.Logger]): Logger instance
        """
        self.logger = logger or setup_logger("scheduler")
        self.running = False
        self.scheduler_thread = None
        self.lock = threading.Lock()
    
    def start(self) -> None:
        """
        Start the scheduler thread.
        """
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Scheduler started")
    
    def stop(self) -> None:
        """
        Stop the scheduler thread.
        """
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            self.scheduler_thread = None
        self.logger.info("Scheduler stopped")
    
    def _run_scheduler(self) -> None:
        """
        Run the scheduler loop.
        This method runs in a separate thread.
        """
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in scheduler: {str(e)}")
    
    def schedule_task(self, task: Callable, interval: str, task_id: str) -> bool:
        """
        Schedule a task to run at a specified interval.
        
        Args:
            task (Callable): Task function to run
            interval (str): Interval specification (e.g., '1m', '1h', '1d')
            task_id (str): Unique identifier for the task
            
        Returns:
            bool: True if task was scheduled successfully, False otherwise
        """
        try:
            # Parse interval
            interval_value = int(interval[:-1])
            interval_unit = interval[-1].lower()
            
            # Create a wrapper function that logs exceptions
            def task_wrapper():
                try:
                    self.logger.debug(f"Running scheduled task: {task_id}")
                    task()
                except Exception as e:
                    self.logger.error(f"Error in scheduled task {task_id}: {str(e)}")
            
            # Schedule the task based on the interval unit
            if interval_unit == 'm':
                job = schedule.every(interval_value).minutes.do(task_wrapper)
            elif interval_unit == 'h':
                job = schedule.every(interval_value).hours.do(task_wrapper)
            elif interval_unit == 'd':
                job = schedule.every(interval_value).days.do(task_wrapper)
            else:
                self.logger.error(f"Invalid interval unit: {interval_unit}")
                return False
            
            # Store the job with its ID
            job.tag(task_id)
            
            self.logger.info(f"Scheduled task {task_id} to run every {interval}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error scheduling task {task_id}: {str(e)}")
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            task_id (str): ID of the task to cancel
            
        Returns:
            bool: True if task was cancelled successfully, False otherwise
        """
        try:
            # Get all jobs with the specified tag
            jobs = schedule.get_jobs(task_id)
            
            if not jobs:
                self.logger.warning(f"No scheduled task found with ID: {task_id}")
                return False
            
            # Cancel all jobs with the specified tag
            for job in jobs:
                schedule.cancel_job(job)
            
            self.logger.info(f"Cancelled scheduled task: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        List all scheduled tasks.
        
        Returns:
            List[Dict[str, Any]]: List of scheduled tasks with their details
        """
        tasks = []
        
        for job in schedule.get_jobs():
            # Get the job's tags (we use the first tag as the task ID)
            tags = job.tags
            task_id = tags[0] if tags else "unknown"
            
            # Get the job's interval
            interval = str(job)
            
            tasks.append({
                'task_id': task_id,
                'interval': interval,
                'next_run': job.next_run
            })
        
        return tasks

