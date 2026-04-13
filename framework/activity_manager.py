#!/usr/bin/env python3
"""
Android Activity Manager - Complete Implementation
Manages activity lifecycle, intents, and app components
"""
import os
import sys
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto


class ActivityState(Enum):
    """Activity lifecycle states."""
    CREATED = auto()
    STARTED = auto()
    RESUMED = auto()
    PAUSED = auto()
    STOPPED = auto()
    DESTROYED = auto()


@dataclass
class Intent:
    """Android Intent - describes operation to perform."""
    action: str = ""
    data: str = ""  # URI
    type: str = ""  # MIME type
    component: str = ""  # Target class name
    flags: int = 0
    extras: Dict[str, Any] = field(default_factory=dict)
    categories: List[str] = field(default_factory=list)
    
    def putExtra(self, name: str, value: Any):
        """Add extra data to intent."""
        self.extras[name] = value
        return self
    
    def getStringExtra(self, name: str) -> Optional[str]:
        """Get string extra."""
        val = self.extras.get(name)
        return str(val) if val is not None else None
    
    def getIntExtra(self, name: str, defaultValue: int = 0) -> int:
        """Get int extra."""
        val = self.extras.get(name)
        return int(val) if val is not None else defaultValue
    
    def setClassName(self, packageName: str, className: str):
        """Set explicit component."""
        self.component = f"{packageName}/{className}"
    
    def setAction(self, action: str):
        """Set action."""
        self.action = action
    
    def setData(self, data: str):
        """Set data URI."""
        self.data = data
    
    def addCategory(self, category: str):
        """Add category to intent."""
        self.categories.append(category)


@dataclass
class ActivityRecord:
    """Record of a running activity."""
    activity_id: int
    class_name: str
    package_name: str
    intent: Intent
    state: ActivityState = ActivityState.CREATED
    instance: Any = None  # Python activity object
    task_id: int = 0
    
    def __post_init__(self):
        self.state = ActivityState.CREATED


class ActivityManager:
    """
    Complete Android Activity Manager implementation.
    Handles activity lifecycle, back stack, and task management.
    """
    
    # Intent actions
    ACTION_MAIN = "android.intent.action.MAIN"
    ACTION_VIEW = "android.intent.action.VIEW"
    ACTION_SEND = "android.intent.action.SEND"
    ACTION_EDIT = "android.intent.action.EDIT"
    ACTION_PICK = "android.intent.action.PICK"
    
    # Intent categories
    CATEGORY_DEFAULT = "android.intent.category.DEFAULT"
    CATEGORY_LAUNCHER = "android.intent.category.LAUNCHER"
    CATEGORY_HOME = "android.intent.category.HOME"
    
    # Flags
    FLAG_ACTIVITY_NEW_TASK = 0x10000000
    FLAG_ACTIVITY_CLEAR_TOP = 0x04000000
    FLAG_ACTIVITY_SINGLE_TOP = 0x20000000
    
    def __init__(self):
        self.next_activity_id = 1
        self.activities: Dict[int, ActivityRecord] = {}
        self.task_stack: List[int] = []  # Activity IDs in order
        self.loaded_classes: Dict[str, type] = {}  # class_name -> class
        self.package_manager = None
        self.system_context = None
        
        # Lifecycle callbacks
        self.lifecycle_callbacks: Dict[str, List[Callable]] = {
            'onCreate': [],
            'onStart': [],
            'onResume': [],
            'onPause': [],
            'onStop': [],
            'onDestroy': [],
        }
    
    def register_activity_class(self, class_name: str, clazz: type):
        """Register an activity class that can be instantiated."""
        self.loaded_classes[class_name] = clazz
        print(f"[*] Registered activity: {class_name}")
    
    def startActivity(self, intent: Intent) -> bool:
        """
        Start an activity based on intent.
        This is the main entry point for launching activities.
        """
        # Resolve intent to component
        component = self._resolve_intent(intent)
        if not component:
            print(f"[!] Cannot resolve intent: {intent.action}")
            return False
        
        # Check if component is registered
        if component not in self.loaded_classes:
            print(f"[!] Activity class not found: '{component}'")
            return False
        
        # Create activity record
        activity_id = self.next_activity_id
        self.next_activity_id += 1
        
        record = ActivityRecord(
            activity_id=activity_id,
            class_name=component,
            package_name=component.split('/')[0] if '/' in component else "unknown",
            intent=intent,
            task_id=1
        )
        
        # Instantiate activity
        try:
            activity_class = self.loaded_classes[component]
            record.instance = activity_class()
            
            # Set context if method exists
            if hasattr(record.instance, 'attachBaseContext') and self.system_context:
                record.instance.attachBaseContext(self.system_context)
            
            self.activities[activity_id] = record
            self.task_stack.append(activity_id)
            
            print(f"[+] Activity created: {component} (ID: {activity_id})")
            
            # Execute lifecycle
            self._execute_lifecycle(record, 'onCreate', intent.extras)
            self._execute_lifecycle(record, 'onStart')
            self._execute_lifecycle(record, 'onResume')
            
            record.state = ActivityState.RESUMED
            return True
            
        except Exception as e:
            print(f"[!] Failed to start activity: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _resolve_intent(self, intent: Intent) -> Optional[str]:
        """Resolve intent to concrete component."""
        # If component explicitly set, use it
        # Format: packageName/className - className may contain /
        if intent.component:
            if '/' in intent.component:
                # Split only on first / to preserve class name with / characters
                return intent.component.split('/', 1)[1]
            return intent.component
        
        # Check for MAIN action with LAUNCHER category
        if intent.action == self.ACTION_MAIN:
            # Find launcher activity
            for class_name in self.loaded_classes:
                if 'MainActivity' in class_name or 'Launcher' in class_name:
                    return class_name
        
        # Default: find any activity
        if self.loaded_classes:
            return list(self.loaded_classes.keys())[0]
        
        return None
    
    def _execute_lifecycle(self, record: ActivityRecord, callback: str, *args):
        """Execute lifecycle callback on activity."""
        instance = record.instance
        if not instance:
            return
        
        # Call method if exists
        method = getattr(instance, callback, None)
        if method and callable(method):
            try:
                method(*args)
                print(f"  -> {record.class_name}.{callback}()")
            except Exception as e:
                print(f"  [!] Error in {callback}: {e}")
        
        # Notify registered callbacks
        for cb in self.lifecycle_callbacks.get(callback, []):
            try:
                cb(record, *args)
            except Exception as e:
                print(f"  [!] Callback error: {e}")
    
    def finishActivity(self, activity_id: int):
        """Finish an activity."""
        if activity_id not in self.activities:
            return
        
        record = self.activities[activity_id]
        
        # Lifecycle: pause -> stop -> destroy
        if record.state == ActivityState.RESUMED:
            self._execute_lifecycle(record, 'onPause')
            record.state = ActivityState.PAUSED
        
        if record.state in [ActivityState.PAUSED, ActivityState.STARTED]:
            self._execute_lifecycle(record, 'onStop')
            record.state = ActivityState.STOPPED
        
        self._execute_lifecycle(record, 'onDestroy')
        record.state = ActivityState.DESTROYED
        
        # Remove from stack
        if activity_id in self.task_stack:
            self.task_stack.remove(activity_id)
        
        # Clean up
        del self.activities[activity_id]
        
        print(f"[*] Activity finished: {record.class_name}")
        
        # Resume previous activity if any
        if self.task_stack:
            prev_id = self.task_stack[-1]
            prev_record = self.activities.get(prev_id)
            if prev_record and prev_record.state == ActivityState.STOPPED:
                self._execute_lifecycle(prev_record, 'onRestart')
                self._execute_lifecycle(prev_record, 'onStart')
                self._execute_lifecycle(prev_record, 'onResume')
                prev_record.state = ActivityState.RESUMED
    
    def getCurrentActivity(self) -> Optional[ActivityRecord]:
        """Get the currently resumed activity."""
        if not self.task_stack:
            return None
        
        current_id = self.task_stack[-1]
        return self.activities.get(current_id)
    
    def registerLifecycleCallback(self, event: str, callback: Callable):
        """Register a lifecycle callback."""
        if event in self.lifecycle_callbacks:
            self.lifecycle_callbacks[event].append(callback)
    
    def dump_stack(self):
        """Print current activity stack."""
        print("\n=== Activity Stack ===")
        for i, activity_id in enumerate(reversed(self.task_stack)):
            record = self.activities.get(activity_id)
            if record:
                prefix = ">" if i == 0 else " "
                print(f"{prefix} [{activity_id}] {record.class_name} ({record.state.name})")
        print()
    
    def getActivityCount(self) -> int:
        """Get number of running activities."""
        return len(self.activities)


# Export
__all__ = ['ActivityManager', 'ActivityRecord', 'Intent', 'ActivityState']
