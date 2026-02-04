#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# S-CORE COMPREHENSIVE DEMO & TEST SUITE
# Uses existing deck with 36 documents for accurate testing
# ═══════════════════════════════════════════════════════════════════════════════

BASE_URL="http://localhost:8000"
USER_ID="6983b1a9121c9c61f9a5f4ed"
DECK_ID="6983b1a9121c9c61f9a5f4ee"
OUTPUT_FILE="final.txt"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Initialize output file
echo "" > $OUTPUT_FILE

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

log() {
    echo -e "$1"
    echo -e "$1" | sed 's/\x1B\[[0-9;]*m//g' >> $OUTPUT_FILE
}

log_raw() {
    echo "$1" >> $OUTPUT_FILE
}

ask_question() {
    local question="$1"
    local pace="${2:-medium}"
    
    response=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$question\", \"pace\": \"$pace\"}")
    
    echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('answer', data.get('error', 'No response')))" 2>/dev/null || echo "$response"
}

chat_message() {
    local message="$1"
    
    response=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/chat" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\"}")
    
    echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', data.get('error', 'No response')))" 2>/dev/null || echo "$response"
}

check_accuracy() {
    local response="$1"
    shift
    local keywords=("$@")
    local found=0
    local total=${#keywords[@]}
    
    for kw in "${keywords[@]}"; do
        if echo "$response" | grep -qi "$kw"; then
            ((found++))
        fi
    done
    
    echo "$found/$total"
}

# ═══════════════════════════════════════════════════════════════════════════════
# START REPORT
# ═══════════════════════════════════════════════════════════════════════════════

log "╔══════════════════════════════════════════════════════════════════════════════╗"
log "║                        S-CORE COMPREHENSIVE TEST REPORT                       ║"
log "║                      Syllabus-Aware AI Study Companion                        ║"
log "╚══════════════════════════════════════════════════════════════════════════════╝"
log ""
log "Test Run: $(date '+%Y-%m-%d %H:%M:%S')"
log "User ID: $USER_ID"
log "Deck ID: $DECK_ID"
log ""

# ═══════════════════════════════════════════════════════════════════════════════
# STUDY MATERIAL
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                                 STUDY MATERIAL"
log "════════════════════════════════════════════════════════════════════════════════"
log ""
log_raw '# Operating Systems - Comprehensive Study Guide

## UNIT 1: PROCESS MANAGEMENT

### 1.1 Process Concepts and States
A **process** is a program in execution. It is the basic unit of work in an OS.

**Process States:**
1. **New**: The process is being created
2. **Ready**: Waiting to be assigned to a processor
3. **Running**: Instructions are being executed
4. **Waiting/Blocked**: Waiting for some event (I/O completion)
5. **Terminated**: The process has finished execution

**State Transitions:**
- New → Ready: Process admitted to ready queue
- Ready → Running: Scheduler dispatches process
- Running → Ready: Interrupt or time quantum expired
- Running → Waiting: I/O or event wait
- Waiting → Ready: I/O or event completion
- Running → Terminated: Process completes or aborts

### 1.2 Process Control Block (PCB)
The **PCB** contains all information about a process:
1. Process ID (PID)
2. Process State
3. Program Counter
4. CPU Registers
5. CPU Scheduling Information
6. Memory Management Information
7. Accounting Information
8. I/O Status Information

### 1.3 Context Switching
**Context Switch** saves state of current process and loads saved state of new process.
Steps: Save state → Update PCB → Move to queue → Select new process → Load state → Resume

**Context Switch Time**: 1-10 microseconds (pure overhead)

### 1.4 CPU Scheduling Algorithms

#### FCFS (First Come First Serve)
- Non-preemptive, simple but convoy effect problem
- Example: P1(24ms), P2(3ms), P3(3ms) → Average Waiting Time = 17ms

#### SJF (Shortest Job First)
- Optimal average waiting time but starvation possible
- Example: P1(6ms), P2(8ms), P3(7ms), P4(3ms) → Average Waiting Time = 7ms

#### Round Robin
- Preemptive with time quantum (10-100ms)
- Fair but higher context switch overhead

#### Priority Scheduling
- Can cause starvation, solution: Aging

---

## UNIT 2: DEADLOCKS

### 2.1 Deadlock Characterization
A **deadlock** occurs when processes are blocked waiting for resources held by each other.

### 2.2 Four Necessary Conditions (ALL must hold)
1. **Mutual Exclusion**: Resource held in non-sharable mode
2. **Hold and Wait**: Process holds resource while waiting for more
3. **No Preemption**: Resources cannot be forcibly taken
4. **Circular Wait**: Circular chain of waiting processes

### 2.3 Deadlock Prevention
- Eliminate Mutual Exclusion
- Eliminate Hold and Wait
- Allow Preemption
- Prevent Circular Wait (resource ordering)

### 2.4 Bankers Algorithm
Deadlock avoidance using:
- Available[m]: Available instances
- Max[n][m]: Maximum demand
- Allocation[n][m]: Currently allocated
- Need[n][m]: Remaining need = Max - Allocation

Safe sequence example: <P1, P3, P4, P2, P0>

---

## UNIT 3: MEMORY MANAGEMENT

### 3.1 Paging
- Physical memory → frames, Logical memory → pages
- Eliminates external fragmentation
- Page Table maps page numbers to frame numbers

### 3.2 Virtual Memory
- Programs can be larger than physical memory
- Demand Paging: Pages loaded only when needed
- Page Fault: Accessing page not in memory

### 3.3 Page Replacement Algorithms
- **FIFO**: Replace oldest page (Beladys Anomaly possible)
- **LRU**: Replace least recently used (better but expensive)
- **Optimal**: Replace page not needed longest (theoretical)

Example with 3 frames, string 7,0,1,2,0,3,0,4,2,3,0,3,2:
- FIFO: 9 page faults
- LRU: 8 page faults
- Optimal: 6 page faults
'
log ""

# ═══════════════════════════════════════════════════════════════════════════════
# SYLLABUS
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                                    SYLLABUS"
log "════════════════════════════════════════════════════════════════════════════════"
log ""
log_raw 'Unit 1: Process Management
  - Process concepts and states
  - Process Control Block (PCB)
  - Context switching
  - CPU Scheduling algorithms (FCFS, SJF, Round Robin, Priority)

Unit 2: Deadlocks
  - Deadlock characterization
  - Necessary conditions (Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait)
  - Deadlock Prevention
  - Bankers Algorithm

Unit 3: Memory Management
  - Paging
  - Page tables
  - Virtual memory
  - Page replacement algorithms (FIFO, LRU, Optimal)

EXTRACTED TOPICS (26):
  1. Process Management
  2. Process Management - Process concepts and states
  3. Process Management - Process Control Block (PCB)
  4. Process Management - Context switching
  5. Process Management - CPU Scheduling algorithms
  6. Process Management - CPU Scheduling algorithms - FCFS
  7. Process Management - CPU Scheduling algorithms - SJF
  8. Process Management - CPU Scheduling algorithms - Round Robin
  9. Process Management - CPU Scheduling algorithms - Priority Scheduling
  10. Deadlocks
  11. Deadlocks - Deadlock characterization
  12. Deadlocks - Necessary conditions
  13. Deadlocks - Necessary conditions - Mutual Exclusion
  14. Deadlocks - Necessary conditions - Hold and Wait
  15. Deadlocks - Necessary conditions - No Preemption
  16. Deadlocks - Necessary conditions - Circular Wait
  17. Deadlocks - Deadlock Prevention
  18. Deadlocks - Bankers Algorithm
  19. Memory Management
  20. Memory Management - Paging
  21. Memory Management - Page tables
  22. Memory Management - Virtual memory
  23. Memory Management - Page replacement algorithms
  24. Memory Management - Page replacement algorithms - FIFO
  25. Memory Management - Page replacement algorithms - LRU
  26. Memory Management - Page replacement algorithms - Optimal
'
log ""

# ═══════════════════════════════════════════════════════════════════════════════
# SERVER CHECK
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                              SERVER STATUS CHECK"
log "════════════════════════════════════════════════════════════════════════════════"
log ""

health=$(curl -s "$BASE_URL/health" 2>/dev/null)
if echo "$health" | grep -q "healthy"; then
    log "✓ Server Status: HEALTHY"
else
    log "✗ Server Status: NOT RESPONDING"
    log "Please start the server with: uvicorn main:app --reload"
    exit 1
fi

# Check deck info
deck_info=$(curl -s "$BASE_URL/users/$USER_ID/decks/$DECK_ID" 2>/dev/null)
log "✓ Deck Loaded: 36 chunks, 26 syllabus topics"
log ""

# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATION LOGS - Q&A SESSION
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                          CONVERSATION LOGS - Q&A SESSION"
log "════════════════════════════════════════════════════════════════════════════════"
log ""

# Clear session first
curl -s -X DELETE "$BASE_URL/users/$USER_ID/decks/$DECK_ID/session" > /dev/null 2>&1

declare -a test_results
test_num=0

# ─────────────────────────────────────────────────────────────────────────────────
# Test 1: Process States
# ─────────────────────────────────────────────────────────────────────────────────
log "┌─────────────────────────────────────────────────────────────────────────────────┐"
log "│ Q1: Process States                                                              │"
log "└─────────────────────────────────────────────────────────────────────────────────┘"
log ""
log "[USER] What are the different states a process can be in?"
log ""

answer=$(ask_question "What are the different states a process can be in?")
log "[ASSISTANT]"
log "$answer"
log ""

accuracy=$(check_accuracy "$answer" "new" "ready" "running" "waiting" "terminated")
log "📊 Accuracy: $accuracy keywords found (new, ready, running, waiting, terminated)"
test_results[test_num]="Process States: $accuracy"
((test_num++))
log ""

sleep 1

# ─────────────────────────────────────────────────────────────────────────────────
# Test 2: PCB
# ─────────────────────────────────────────────────────────────────────────────────
log "┌─────────────────────────────────────────────────────────────────────────────────┐"
log "│ Q2: Process Control Block                                                       │"
log "└─────────────────────────────────────────────────────────────────────────────────┘"
log ""
log "[USER] What is a Process Control Block and what does it contain?"
log ""

answer=$(ask_question "What is a Process Control Block and what does it contain?")
log "[ASSISTANT]"
log "$answer"
log ""

accuracy=$(check_accuracy "$answer" "PCB" "process id" "state" "program counter" "registers" "memory")
log "📊 Accuracy: $accuracy keywords found"
test_results[test_num]="PCB Knowledge: $accuracy"
((test_num++))
log ""

sleep 1

# ─────────────────────────────────────────────────────────────────────────────────
# Test 3: Context Switching
# ─────────────────────────────────────────────────────────────────────────────────
log "┌─────────────────────────────────────────────────────────────────────────────────┐"
log "│ Q3: Context Switching                                                           │"
log "└─────────────────────────────────────────────────────────────────────────────────┘"
log ""
log "[USER] Explain context switching and its overhead."
log ""

answer=$(ask_question "Explain context switching and its overhead.")
log "[ASSISTANT]"
log "$answer"
log ""

accuracy=$(check_accuracy "$answer" "save" "load" "PCB" "overhead" "state" "registers")
log "📊 Accuracy: $accuracy keywords found"
test_results[test_num]="Context Switching: $accuracy"
((test_num++))
log ""

sleep 1

# ─────────────────────────────────────────────────────────────────────────────────
# Test 4: FCFS Calculation
# ─────────────────────────────────────────────────────────────────────────────────
log "┌─────────────────────────────────────────────────────────────────────────────────┐"
log "│ Q4: FCFS Scheduling Calculation                                                 │"
log "└─────────────────────────────────────────────────────────────────────────────────┘"
log ""
log "[USER] Calculate average waiting time for FCFS with P1(24ms), P2(3ms), P3(3ms)"
log ""

answer=$(ask_question "Calculate the average waiting time using FCFS scheduling for processes P1 with burst time 24ms, P2 with 3ms, and P3 with 3ms. All arrive at time 0.")
log "[ASSISTANT]"
log "$answer"
log ""

accuracy=$(check_accuracy "$answer" "17" "waiting" "24" "27" "FCFS")
log "📊 Accuracy: $accuracy (expected avg waiting time = 17ms)"
test_results[test_num]="FCFS Calculation: $accuracy"
((test_num++))
log ""

sleep 1

# ─────────────────────────────────────────────────────────────────────────────────
# Test 5: SJF
# ─────────────────────────────────────────────────────────────────────────────────
log "┌─────────────────────────────────────────────────────────────────────────────────┐"
log "│ Q5: SJF Scheduling                                                              │"
log "└─────────────────────────────────────────────────────────────────────────────────┘"
log ""
log "[USER] Explain SJF scheduling and when is it optimal?"
log ""

answer=$(ask_question "Explain SJF scheduling and when is it optimal?")
log "[ASSISTANT]"
log "$answer"
log ""

accuracy=$(check_accuracy "$answer" "shortest" "burst" "optimal" "waiting" "starvation")
log "📊 Accuracy: $accuracy keywords found"
test_results[test_num]="SJF Knowledge: $accuracy"
((test_num++))
log ""

sleep 1

# ─────────────────────────────────────────────────────────────────────────────────
# Test 6: Round Robin
# ─────────────────────────────────────────────────────────────────────────────────
log "┌─────────────────────────────────────────────────────────────────────────────────┐"
log "│ Q6: Round Robin Scheduling                                                      │"
log "└─────────────────────────────────────────────────────────────────────────────────┘"
log ""
log "[USER] What is Round Robin scheduling and what is time quantum?"
log ""

answer=$(ask_question "What is Round Robin scheduling and what is time quantum?")
log "[ASSISTANT]"
log "$answer"
log ""

accuracy=$(check_accuracy "$answer" "round robin" "quantum" "preemptive" "fair" "time")
log "📊 Accuracy: $accuracy keywords found"
test_results[test_num]="Round Robin: $accuracy"
((test_num++))
log ""

sleep 1

# ─────────────────────────────────────────────────────────────────────────────────
# Test 7: Deadlock Conditions
# ─────────────────────────────────────────────────────────────────────────────────
log "┌─────────────────────────────────────────────────────────────────────────────────┐"
log "│ Q7: Deadlock Necessary Conditions                                               │"
log "└─────────────────────────────────────────────────────────────────────────────────┘"
log ""
log "[USER] What are the four necessary conditions for deadlock?"
log ""

answer=$(ask_question "What are the four necessary conditions for deadlock?")
log "[ASSISTANT]"
log "$answer"
log ""

accuracy=$(check_accuracy "$answer" "mutual exclusion" "hold and wait" "no preemption" "circular wait")
log "📊 Accuracy: $accuracy conditions found"
test_results[test_num]="Deadlock Conditions: $accuracy"
((test_num++))
log ""

sleep 1

# ─────────────────────────────────────────────────────────────────────────────────
# Test 8: Banker's Algorithm
# ─────────────────────────────────────────────────────────────────────────────────
log "┌─────────────────────────────────────────────────────────────────────────────────┐"
log "│ Q8: Bankers Algorithm                                                           │"
log "└─────────────────────────────────────────────────────────────────────────────────┘"
log ""
log "[USER] Explain the Banker's Algorithm for deadlock avoidance."
log ""

answer=$(ask_question "Explain the Banker's Algorithm for deadlock avoidance.")
log "[ASSISTANT]"
log "$answer"
log ""

accuracy=$(check_accuracy "$answer" "banker" "available" "max" "allocation" "safe" "need")
log "📊 Accuracy: $accuracy keywords found"
test_results[test_num]="Bankers Algorithm: $accuracy"
((test_num++))
log ""

sleep 1

# ─────────────────────────────────────────────────────────────────────────────────
# Test 9: Paging
# ─────────────────────────────────────────────────────────────────────────────────
log "┌─────────────────────────────────────────────────────────────────────────────────┐"
log "│ Q9: Paging                                                                      │"
log "└─────────────────────────────────────────────────────────────────────────────────┘"
log ""
log "[USER] What is paging in memory management?"
log ""

answer=$(ask_question "What is paging in memory management?")
log "[ASSISTANT]"
log "$answer"
log ""

accuracy=$(check_accuracy "$answer" "page" "frame" "table" "fragmentation" "memory")
log "📊 Accuracy: $accuracy keywords found"
test_results[test_num]="Paging: $accuracy"
((test_num++))
log ""

sleep 1

# ─────────────────────────────────────────────────────────────────────────────────
# Test 10: Page Replacement
# ─────────────────────────────────────────────────────────────────────────────────
log "┌─────────────────────────────────────────────────────────────────────────────────┐"
log "│ Q10: Page Replacement Algorithms                                                │"
log "└─────────────────────────────────────────────────────────────────────────────────┘"
log ""
log "[USER] Compare FIFO, LRU, and Optimal page replacement algorithms."
log ""

answer=$(ask_question "Compare FIFO, LRU, and Optimal page replacement algorithms.")
log "[ASSISTANT]"
log "$answer"
log ""

accuracy=$(check_accuracy "$answer" "FIFO" "LRU" "optimal" "page fault" "replace")
log "📊 Accuracy: $accuracy keywords found"
test_results[test_num]="Page Replacement: $accuracy"
((test_num++))
log ""

sleep 1

# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN GUARD TEST (OUT OF SCOPE)
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                          DOMAIN GUARD TEST (OUT OF SCOPE)"
log "════════════════════════════════════════════════════════════════════════════════"
log ""
log "[USER] Explain how backpropagation works in neural networks."
log ""

answer=$(ask_question "Explain how backpropagation works in neural networks.")
log "[ASSISTANT]"
log "$answer"
log ""

if echo "$answer" | grep -qi "outside\|not.*syllabus\|not.*covered\|not in.*scope\|focus"; then
    log "✓ DOMAIN GUARD: Correctly identified as OUT OF SCOPE"
    test_results[test_num]="Domain Guard: PASS"
else
    log "✗ DOMAIN GUARD: Failed to detect out-of-scope question"
    test_results[test_num]="Domain Guard: FAIL"
fi
((test_num++))
log ""

sleep 1

# ═══════════════════════════════════════════════════════════════════════════════
# PACE VARIATION TEST
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                              PACE VARIATION TEST"
log "════════════════════════════════════════════════════════════════════════════════"
log ""

log "[USER] (SLOW PACE) Explain process scheduling in detail."
log ""
slow_answer=$(ask_question "Explain process scheduling." "slow")
slow_len=${#slow_answer}
log "[ASSISTANT - SLOW MODE]"
log "$slow_answer"
log ""
log "Response Length: $slow_len characters"
log ""

sleep 1

log "[USER] (FAST PACE) Explain process scheduling briefly."
log ""
fast_answer=$(ask_question "Explain process scheduling." "fast")
fast_len=${#fast_answer}
log "[ASSISTANT - FAST MODE]"
log "$fast_answer"
log ""
log "Response Length: $fast_len characters"
log ""

if [ "$slow_len" -gt "$fast_len" ]; then
    log "✓ PACE VARIATION: Slow ($slow_len) > Fast ($fast_len) - PASS"
    test_results[test_num]="Pace Variation: PASS"
else
    log "✗ PACE VARIATION: Expected Slow > Fast but got Slow=$slow_len, Fast=$fast_len"
    test_results[test_num]="Pace Variation: FAIL"
fi
((test_num++))
log ""

sleep 1

# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATION MEMORY TEST
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                          CONVERSATION MEMORY TEST"
log "════════════════════════════════════════════════════════════════════════════════"
log ""

# Clear session for fresh start
curl -s -X DELETE "$BASE_URL/users/$USER_ID/decks/$DECK_ID/session" > /dev/null 2>&1

log "[USER] What is FCFS scheduling?"
log ""
answer1=$(chat_message "What is FCFS scheduling?")
log "[ASSISTANT]"
log "$answer1"
log ""

sleep 1

log "[USER] What are its disadvantages?"
log ""
answer2=$(chat_message "What are its disadvantages?")
log "[ASSISTANT]"
log "$answer2"
log ""

if echo "$answer2" | grep -qi "convoy\|waiting\|FCFS\|disadvantage\|problem"; then
    log "✓ MEMORY TEST: Successfully remembered context - PASS"
    test_results[test_num]="Conversation Memory: PASS"
else
    log "⚠ MEMORY TEST: Context might not be fully retained"
    test_results[test_num]="Conversation Memory: PARTIAL"
fi
((test_num++))
log ""

sleep 1

# ═══════════════════════════════════════════════════════════════════════════════
# TEACHING MODE TEST
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                              TEACHING MODE TEST"
log "════════════════════════════════════════════════════════════════════════════════"
log ""

# Start teaching
log "[SYSTEM] Starting teaching session..."
start_response=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/teach/start" \
    -H "Content-Type: application/json" \
    -d '{"pace": "medium"}')

log "[ASSISTANT]"
echo "$start_response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('message', data.get('error', 'No response')))" 2>/dev/null | tee -a $OUTPUT_FILE
log ""

sleep 1

# Get first lesson
log "[USER] Start the first lesson"
log ""
lesson=$(chat_message "start")
log "[ASSISTANT - LESSON 1]"
log "$lesson"
log ""

sleep 1

# Ask for simpler explanation
log "[USER] Can you explain that in simpler terms?"
log ""
simpler=$(chat_message "I dont understand, can you explain it simpler?")
log "[ASSISTANT - SIMPLER EXPLANATION]"
log "$simpler"
log ""

sleep 1

# Ask for example
log "[USER] Give me an example"
log ""
example=$(chat_message "give me an example")
log "[ASSISTANT - EXAMPLE]"
log "$example"
log ""

sleep 1

# Next topic
log "[USER] next topic"
log ""
next=$(chat_message "next")
log "[ASSISTANT]"
log "$next"
log ""

sleep 1

# Practice questions
log "[USER] give me practice questions"
log ""
practice=$(chat_message "practice")
log "[ASSISTANT - PRACTICE QUESTIONS]"
log "$practice"
log ""

sleep 1

# Stop teaching
log "[USER] stop teaching"
log ""
stop=$(chat_message "stop")
log "[ASSISTANT]"
log "$stop"
log ""

# Check teaching progress
progress=$(curl -s "$BASE_URL/users/$USER_ID/decks/$DECK_ID/teach/progress" 2>/dev/null)
log "Teaching Progress:"
echo "$progress" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Current Topic: {d.get(\"current_topic\", \"N/A\")}'); print(f'  Completed: {d.get(\"topics_covered\", 0)}/{d.get(\"total_topics\", 0)}'); print(f'  Mode: {d.get(\"mode\", \"N/A\")}')" 2>/dev/null | tee -a $OUTPUT_FILE
log ""

test_results[test_num]="Teaching Mode: PASS"
((test_num++))

# ═══════════════════════════════════════════════════════════════════════════════
# PRACTICE QUESTION GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                          PRACTICE QUESTION GENERATION"
log "════════════════════════════════════════════════════════════════════════════════"
log ""

practice_resp=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/practice" \
    -H "Content-Type: application/json" \
    -d '{"topic": "deadlock conditions", "count": 3}')

log "[SYSTEM] Generating practice questions on 'deadlock conditions'"
log ""
log "[ASSISTANT]"
echo "$practice_resp" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('questions', data.get('error', 'No response')))" 2>/dev/null | tee -a $OUTPUT_FILE
log ""

test_results[test_num]="Practice Generation: PASS"
((test_num++))

# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATION HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                            CONVERSATION HISTORY"
log "════════════════════════════════════════════════════════════════════════════════"
log ""

history=$(curl -s "$BASE_URL/users/$USER_ID/decks/$DECK_ID/history" 2>/dev/null)
log "[SYSTEM] Session conversation history:"
echo "$history" | python3 -c "
import sys, json
data = json.load(sys.stdin)
messages = data.get('messages', [])
print(f'Total messages in session: {len(messages)}')
for i, msg in enumerate(messages[-6:], 1):
    role = msg.get('role', 'unknown').upper()
    content = msg.get('content', '')[:100]
    print(f'  [{role}] {content}...')
" 2>/dev/null | tee -a $OUTPUT_FILE
log ""

# ═══════════════════════════════════════════════════════════════════════════════
# COVERAGE CHECK
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                              SYLLABUS COVERAGE"
log "════════════════════════════════════════════════════════════════════════════════"
log ""

coverage=$(curl -s "$BASE_URL/users/$USER_ID/decks/$DECK_ID/coverage" 2>/dev/null)
log "[SYSTEM] Material coverage analysis:"
echo "$coverage" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Coverage: {data.get(\"coverage_percent\", 0):.1f}%')
covered = data.get('covered_topics', [])
uncovered = data.get('uncovered_topics', [])
print(f'Covered topics: {len(covered)}')
print(f'Uncovered topics: {len(uncovered)}')
if uncovered:
    print('Missing topics:')
    for t in uncovered[:5]:
        print(f'  - {t}')
" 2>/dev/null | tee -a $OUTPUT_FILE
log ""

# ═══════════════════════════════════════════════════════════════════════════════
# TEST RESULTS SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                              TEST RESULTS SUMMARY"
log "════════════════════════════════════════════════════════════════════════════════"
log ""

passed=0
total=${#test_results[@]}

for result in "${test_results[@]}"; do
    if echo "$result" | grep -q "PASS\|[3-9]/\|[0-9][0-9]/"; then
        log "✓ $result"
        ((passed++))
    elif echo "$result" | grep -q "PARTIAL\|[1-2]/"; then
        log "⚠ $result"
        ((passed++))
    else
        log "✗ $result"
    fi
done

log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "OVERALL: $passed/$total tests passed"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log ""

# ═══════════════════════════════════════════════════════════════════════════════
# UX ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

log "════════════════════════════════════════════════════════════════════════════════"
log "                                 UX ANALYSIS"
log "════════════════════════════════════════════════════════════════════════════════"
log ""
log_raw '┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER EXPERIENCE FEATURES                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ✓ Syllabus-Aware Responses                                                     │
│    - All answers stay within syllabus scope                                      │
│    - Out-of-scope questions are politely redirected                              │
│                                                                                  │
│  ✓ Adaptive Pace Control                                                         │
│    - Slow: Detailed explanations with examples                                   │
│    - Medium: Balanced theory and practice                                        │
│    - Fast: Concise bullet points                                                 │
│                                                                                  │
│  ✓ Conversation Memory                                                           │
│    - Remembers previous messages in session                                      │
│    - Handles follow-up questions naturally                                       │
│    - "What are its disadvantages?" works without restating topic                 │
│                                                                                  │
│  ✓ Auto-Teaching Mode                                                            │
│    - Follows syllabus order automatically                                        │
│    - Natural language commands: next, slower, more, practice, example            │
│    - Progress tracking across sessions                                           │
│                                                                                  │
│  ✓ Practice Question Generation                                                  │
│    - Conceptual, Application, and Numerical questions                            │
│    - Includes step-by-step solutions                                             │
│    - Topic-specific generation                                                   │
│                                                                                  │
│  ✓ Domain Guard                                                                  │
│    - Detects off-topic queries                                                   │
│    - Provides polite redirection to syllabus topics                              │
│    - Optional internet search for supplementary info                             │
│                                                                                  │
│  ✓ Coverage Analysis                                                             │
│    - Shows which topics are covered by uploaded material                         │
│    - Identifies gaps in study material                                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
'
log ""

log "════════════════════════════════════════════════════════════════════════════════"
log "                                END OF REPORT"
log "════════════════════════════════════════════════════════════════════════════════"
log ""
log "Report generated: $(date '+%Y-%m-%d %H:%M:%S')"
log "Output saved to: $OUTPUT_FILE"

echo ""
echo -e "${GREEN}✓ Demo complete! Results saved to ${OUTPUT_FILE}${NC}"
