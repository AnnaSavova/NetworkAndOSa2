from des import SchedulerDES
from process import ProcessStates
from event import Event
from event import EventTypes

class FCFS(SchedulerDES):
    def scheduler_func(self, cur_event):
		#Find the process that is ready in the list of processes and return
        for proc in self.processes: #Because list of processes is organised by descending arrival time, we can just look for the smallest indexed process in the ready state
            if proc.process_state.name == "READY":
                return proc
        pass #Generally shouldn't be called but kept just in case there are no ready processes

    def dispatcher_func(self, cur_process):
        #Change the process selected to be runnning
        index = self.processes.index(cur_process)
        run = ProcessStates.RUNNING
        self.processes[index].process_state = run
        
        #Compute length of time to run and run to completion
        check = cur_process.run_for(cur_process.service_time, self.time)
        #Advance system time to completion of the process
        self.time = self.time + cur_process.service_time
        
        #Set state to terminated and return CPU_DONE event
        self.processes[index].process_state = ProcessStates.TERMINATED
        e = Event(process_id = cur_process.process_id, event_type = EventTypes.PROC_CPU_DONE,
                  event_time = self.time)
        return e


class SJF(SchedulerDES):
    def scheduler_func(self, cur_event):
        #Find the shortest process that is in the ready state to return
        shortest = self.processes[cur_event.process_id] #Set the process referenced in the current event as shortest

        for proc in self.processes:
            if (shortest.process_state != ProcessStates.READY and proc.process_state == ProcessStates.READY):
                shortest = proc #If the initial process has already been handled, set shortest to the first ready process
            if (proc.process_state == ProcessStates.READY) and (proc.remaining_time < shortest.remaining_time) and (proc.remaining_time > 0):
                #Find the shortest ready process to carry out next
                shortest = proc
                
                
        return shortest

    def dispatcher_func(self, cur_process):
        #Change the process selected to be runnning
        index = self.processes.index(cur_process)
        run = ProcessStates.RUNNING
        self.processes[index].process_state = run
        
        #Compute length of time to run and run to completion
        check = cur_process.run_for(cur_process.service_time, self.time)
        #Advance clock to completion of process
        self.time = self.time + cur_process.service_time
        
        #Set state to terminated and return CPU_DONE event
        self.processes[index].process_state = ProcessStates.TERMINATED
        e = Event(process_id = cur_process.process_id, event_type = EventTypes.PROC_CPU_DONE,
                  event_time = self.time)
        return e


class RR(SchedulerDES):
    def scheduler_func(self, cur_event):
        #Find the first process in the ready state
        for proc in self.processes:
            if proc.process_state == ProcessStates.READY:
                return proc
        pass

    def dispatcher_func(self, cur_process):
        #Change the process selected to be runnning
        index = self.processes.index(cur_process)
        run = ProcessStates.RUNNING
        self.processes[index].process_state = run
        
        #Compute length of time to run, if less than the defined length, run to completion
        default_time = self.quantum
        check = cur_process.run_for(default_time, self.time) #Log amount of time it ran for
        self.time = self.time + check
        
        if check != default_time: #In this case, the process was completed
            self.processes[index].process_state = ProcessStates.TERMINATED
            e = Event(process_id = cur_process.process_id, event_type = EventTypes.PROC_CPU_DONE,
                      event_time = self.time)
            return e
        else: #In this case the process still has time left to run
            self.processes[index].process_state = ProcessStates.READY
            proc = self.processes.pop(index)
            self.processes.append(proc) #Move state to end of the queue
            e = Event(process_id = cur_process.process_id, event_type = EventTypes.PROC_CPU_REQ,
                      event_time = self.time)
            return e

class SRTF(SchedulerDES):
    def scheduler_func(self, cur_event):
        #Find the shortest process in the ready state to run
        if (cur_event.event_type == EventTypes.PROC_ARRIVES): #If a new process arrived while the last was running - ie last did not finish - or has arrived while none were running
            if (self.process_on_cpu != None) and (self.process_on_cpu.process_state != ProcessStates.TERMINATED):
                shortest = self.process_on_cpu #The process tht was running until this one arrived is set as shortest
            else:
                shortest = self.processes[cur_event.process_id] #No process was running when this arrived
            for proc in self.processes:
                if (shortest.process_state != ProcessStates.READY) and (proc.process_state == ProcessStates.READY):
                    shortest = proc #If the event was given out of order, make sure shortest is ready and not already handled
                if (shortest == self.process_on_cpu):
                    if (proc.process_state == ProcessStates.READY) and (proc.remaining_time + self.context_switch_time < shortest.remaining_time):
                        shortest = proc
                else:
                    if (proc.process_state == ProcessStates.READY) and (proc.remaining_time < shortest.remaining_time):
                        shortest = proc
        else: #If the last process terminated before the next arrived or all processes have arrived and the last process terminate
            shortest = self.processes[cur_event.process_id] #The new process that has arrived will be set as shortest
            for proc in self.processes:
                if (shortest.process_state != ProcessStates.READY) and (proc.process_state == ProcessStates.READY):
                    shortest = proc #If the event was a process done event, set the first ready process as shortest
                if (proc.process_state == ProcessStates.READY) and (proc.remaining_time < shortest.remaining_time):
                    shortest = proc
        return shortest

    def dispatcher_func(self, cur_process):
        #Change the process selected to be runnning
        index = self.processes.index(cur_process)
        run = ProcessStates.RUNNING
        self.processes[index].process_state = run
        
        #Run until the next process arrives
        ttr = 0
        for proc in self.processes:
            if proc.process_state == ProcessStates.NEW: #Find first new process
                next = proc.arrival_time #Log when it will arrive
                ttr = next - self.time #Determine length of time between now and then
                break
        if ttr == 0: #In this case, there are no new processes, so run to completion
            ttr = cur_process.remaining_time 
        elif ttr < 0: #It's taken too long
            self.processes[index].process_state = ProcessStates.READY
            e = Event(process_id = cur_process.process_id, event_type = EventTypes.PROC_CPU_REQ,
                      event_time = self.time)
            return e
        
        #Run for the determined length of time
        check = cur_process.run_for(ttr, self.time) #Log amount of time it ran for
        self.time = self.time + check
        
        #Check if process is completed
        if cur_process.remaining_time == 0:
            self.processes[index].process_state = ProcessStates.TERMINATED
            e = Event(process_id = cur_process.process_id, event_type = EventTypes.PROC_CPU_DONE,
                      event_time = self.time)
            return e
        else:
            self.processes[index].process_state = ProcessStates.READY
            e = Event(process_id = cur_process.process_id, event_type = EventTypes.PROC_CPU_REQ,
                      event_time = self.time)
            return e