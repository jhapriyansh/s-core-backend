#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# S-Core Comprehensive API Test Suite
# Tests all features with accuracy analysis
# Generates final.txt with complete demo run log
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

BASE_URL="http://localhost:8000"
USER_ID=""
DECK_ID=""
SESSION_ID=""
FINAL_LOG="/Users/priyanshukumarjha/Code/s-core/backend/final.txt"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters for accuracy
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log() {
    echo "$1" | tee -a "$FINAL_LOG"
}

log_section() {
    echo "" | tee -a "$FINAL_LOG"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$FINAL_LOG"
    echo "$1" | tee -a "$FINAL_LOG"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$FINAL_LOG"
}

check_response() {
    local response="$1"
    local expected_field="$2"
    local test_name="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if echo "$response" | grep -q "$expected_field"; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✓ PASS${NC}: $test_name" | tee -a "$FINAL_LOG"
        return 0
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${RED}✗ FAIL${NC}: $test_name" | tee -a "$FINAL_LOG"
        return 1
    fi
}

check_accuracy() {
    local response="$1"
    local keywords="$2"
    local test_name="$3"
    local found=0
    local total=0
    
    IFS='|' read -ra KEYWORDS <<< "$keywords"
    for keyword in "${KEYWORDS[@]}"; do
        total=$((total + 1))
        if echo "$response" | grep -qi "$keyword"; then
            found=$((found + 1))
        fi
    done
    
    local accuracy=$((found * 100 / total))
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ $accuracy -ge 50 ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✓ ACCURACY${NC}: $test_name - $found/$total keywords ($accuracy%)" | tee -a "$FINAL_LOG"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${YELLOW}⚠ LOW ACCURACY${NC}: $test_name - $found/$total keywords ($accuracy%)" | tee -a "$FINAL_LOG"
    fi
    
    return $accuracy
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Initialize Log File
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cat > "$FINAL_LOG" << 'HEADER'
╔══════════════════════════════════════════════════════════════════════╗
║                    S-CORE COMPREHENSIVE TEST REPORT                   ║
║                  Syllabus-Aware AI Study Companion                    ║
╚══════════════════════════════════════════════════════════════════════╝

HEADER

log "Test Run Started: $TIMESTAMP"
log "Base URL: $BASE_URL"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Server Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "SERVER STATUS CHECK"

if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    log "❌ ERROR: Server not running at $BASE_URL"
    log "Please start the server first: python main.py"
    exit 1
fi
log "✓ Server is running and healthy"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Define Study Material
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYLLABUS="Unit 1: Process Management - Process concepts and states, Process Control Block (PCB), Context switching, CPU Scheduling algorithms (FCFS, SJF, Round Robin, Priority Scheduling). Unit 2: Deadlocks - Deadlock characterization, Necessary conditions (Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait), Deadlock Prevention, Banker's Algorithm. Unit 3: Memory Management - Paging, Page tables, Virtual memory, Page replacement algorithms (FIFO, LRU, Optimal)."

cat > /tmp/os_study_material.txt << 'MATERIAL'
# Operating Systems - Comprehensive Study Guide

## UNIT 1: PROCESS MANAGEMENT

### 1.1 Process Concepts and States

A **process** is a program in execution. It is the basic unit of work in an operating system.

**Process States:**
1. **New**: The process is being created
2. **Ready**: The process is waiting to be assigned to a processor
3. **Running**: Instructions are being executed
4. **Waiting/Blocked**: The process is waiting for some event (I/O completion)
5. **Terminated**: The process has finished execution

**State Transitions:**
- New → Ready: Process admitted to ready queue
- Ready → Running: Scheduler dispatches process
- Running → Ready: Interrupt or time quantum expired
- Running → Waiting: I/O or event wait
- Waiting → Ready: I/O or event completion
- Running → Terminated: Process completes or aborts

### 1.2 Process Control Block (PCB)

The **PCB** is a data structure that contains all information about a process:

1. **Process ID (PID)**: Unique identifier
2. **Process State**: Current state (new, ready, running, etc.)
3. **Program Counter**: Address of next instruction
4. **CPU Registers**: Contents of all process-centric registers
5. **CPU Scheduling Information**: Priority, pointers to scheduling queues
6. **Memory Management Information**: Page tables, segment tables
7. **Accounting Information**: CPU time used, time limits
8. **I/O Status Information**: List of I/O devices allocated

### 1.3 Context Switching

**Context Switch** is the process of saving the state of a currently running process and loading the saved state of a new process.

**Steps in Context Switching:**
1. Save the state of the current process (registers, PC, etc.) to its PCB
2. Update the PCB with the new state (ready/waiting)
3. Move the PCB to appropriate queue
4. Select a new process from ready queue
5. Update PCB of new process to running
6. Load the saved state of new process from its PCB
7. Resume execution of new process

**Context Switch Time**: Typically 1-10 microseconds. This is pure overhead as no useful work is done during switching.

### 1.4 CPU Scheduling Algorithms

#### FCFS (First Come First Serve)
- **Type**: Non-preemptive
- **Mechanism**: Processes are executed in the order they arrive
- **Advantages**: Simple to implement
- **Disadvantages**: Convoy effect (short processes wait behind long ones)

**Example Calculation:**
Processes: P1(24ms), P2(3ms), P3(3ms) arriving at time 0
- P1: Waiting time = 0ms
- P2: Waiting time = 24ms
- P3: Waiting time = 27ms
- **Average Waiting Time = (0 + 24 + 27) / 3 = 17ms**

#### SJF (Shortest Job First)
- **Type**: Can be preemptive (SRTF) or non-preemptive
- **Mechanism**: Process with smallest burst time is selected next
- **Advantages**: Optimal average waiting time
- **Disadvantages**: Starvation of long processes, burst time prediction difficult

**Non-preemptive SJF Example:**
Processes: P1(6ms), P2(8ms), P3(7ms), P4(3ms) arriving at time 0
Order: P4 → P1 → P3 → P2
- P4: 0ms, P1: 3ms, P3: 9ms, P2: 16ms
- **Average Waiting Time = (3 + 16 + 9 + 0) / 4 = 7ms**

#### Round Robin (RR)
- **Type**: Preemptive
- **Mechanism**: Each process gets a fixed time quantum (typically 10-100ms)
- **Advantages**: Fair allocation, good response time
- **Disadvantages**: Higher context switching overhead

**Example with quantum = 4ms:**
Processes: P1(24ms), P2(3ms), P3(3ms)
Execution order: P1(4) → P2(3) → P3(3) → P1(4) → P1(4) → P1(4) → P1(4) → P1(4)
- P1: Completes at 30ms, arrival 0, burst 24 → Turnaround = 30ms
- P2: Completes at 7ms → Turnaround = 7ms
- P3: Completes at 10ms → Turnaround = 10ms
- **Average Turnaround = (30 + 7 + 10) / 3 = 15.67ms**

#### Priority Scheduling
- **Type**: Can be preemptive or non-preemptive
- **Mechanism**: Process with highest priority is selected
- **Problem**: Starvation - low priority processes may never execute
- **Solution**: Aging - gradually increase priority of waiting processes

---

## UNIT 2: DEADLOCKS

### 2.1 Deadlock Characterization

A **deadlock** is a situation where a set of processes are blocked because each process is holding a resource and waiting for another resource held by another process.

**Example**: Process P1 holds Resource R1 and waits for R2. Process P2 holds R2 and waits for R1.

### 2.2 Necessary Conditions for Deadlock

All FOUR conditions must hold simultaneously for deadlock:

1. **Mutual Exclusion**: At least one resource must be held in non-sharable mode
2. **Hold and Wait**: A process holds at least one resource while waiting for additional resources
3. **No Preemption**: Resources cannot be forcibly taken from a process
4. **Circular Wait**: A circular chain of processes exists, each waiting for a resource held by the next

### 2.3 Deadlock Prevention

Prevent deadlock by ensuring at least one necessary condition cannot hold:

1. **Eliminate Mutual Exclusion**: Make resources sharable (not always possible)
2. **Eliminate Hold and Wait**: 
   - Request all resources at once before execution
   - Release all resources before requesting new ones
3. **Allow Preemption**: If a process can't get resources, release what it has
4. **Prevent Circular Wait**: 
   - Order all resources numerically
   - Request resources in increasing order only

### 2.4 Banker's Algorithm

A **deadlock avoidance** algorithm that tests for safety before granting resources.

**Data Structures:**
- **Available[m]**: Available instances of each resource type
- **Max[n][m]**: Maximum demand of each process
- **Allocation[n][m]**: Currently allocated resources
- **Need[n][m]**: Remaining need (Need = Max - Allocation)

**Safety Algorithm:**
1. Initialize Work = Available, Finish[i] = false for all i
2. Find process i where Finish[i] = false AND Need[i] ≤ Work
3. If found: Work = Work + Allocation[i], Finish[i] = true, go to step 2
4. If all Finish[i] = true, system is in SAFE state

**Example:**
Available = [3, 3, 2]
Process  | Allocation | Max    | Need
P0       | [0,1,0]   | [7,5,3] | [7,4,3]
P1       | [2,0,0]   | [3,2,2] | [1,2,2]
P2       | [3,0,2]   | [9,0,2] | [6,0,0]
P3       | [2,1,1]   | [2,2,2] | [0,1,1]
P4       | [0,0,2]   | [4,3,3] | [4,3,1]

Safe sequence: <P1, P3, P4, P2, P0>

---

## UNIT 3: MEMORY MANAGEMENT

### 3.1 Paging

**Paging** is a memory management scheme that eliminates external fragmentation.

- **Physical memory** is divided into fixed-size blocks called **frames**
- **Logical memory** is divided into same-size blocks called **pages**
- **Page size** is typically 4KB or 8KB
- When a process runs, its pages are loaded into available frames

**Address Translation:**
- Logical address = Page number + Page offset
- Physical address = Frame number + Page offset
- Page number is used to index into Page Table

### 3.2 Page Tables

The **Page Table** maps page numbers to frame numbers.

**Page Table Entry (PTE) contains:**
- Frame number
- Valid/Invalid bit
- Protection bits (read/write/execute)
- Modified (dirty) bit
- Reference bit

**Problems with Page Tables:**
1. **Large size**: 32-bit address with 4KB pages needs 2^20 entries
2. **Solutions**: Hierarchical paging, Hashed page tables, Inverted page tables

### 3.3 Virtual Memory

**Virtual Memory** allows execution of processes not completely in memory.

**Benefits:**
- Programs can be larger than physical memory
- More processes can be in memory
- Less I/O needed for loading/swapping

**Demand Paging**: Pages are loaded only when needed (lazy loading)
- **Page Fault**: Occurs when accessing a page not in memory
- OS then loads the required page from disk

### 3.4 Page Replacement Algorithms

When memory is full and a new page is needed, an existing page must be replaced.

#### FIFO (First In First Out)
- Replace the oldest page in memory
- Simple but can suffer from **Belady's Anomaly** (more frames → more faults)

**Example:**
Reference string: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2
Frames = 3
Pages faults = 9

#### LRU (Least Recently Used)
- Replace the page that hasn't been used for the longest time
- Good performance but expensive to implement

**Example:**
Reference string: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2
Frames = 3
Page faults = 8

#### Optimal (OPT)
- Replace the page that will not be used for the longest time in future
- Best possible algorithm but requires future knowledge (not implementable)

**Example:**
Reference string: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2
Frames = 3
Page faults = 6

**Comparison:**
Algorithm | Page Faults | Implementation
FIFO      | 9           | Simple queue
LRU       | 8           | Complex (counters/stack)
Optimal   | 6           | Not possible (theoretical)
MATERIAL

log_section "STUDY MATERIAL"
log "$(cat /tmp/os_study_material.txt)"

log_section "SYLLABUS"
log "$SYLLABUS"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Create User and Deck
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "SETUP: CREATE USER AND DECK"

RANDOM_ID=$RANDOM

# Create user
USER_RESPONSE=$(curl -s -X POST "$BASE_URL/users" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"demo_user_$RANDOM_ID\", \"email\": \"demo$RANDOM_ID@test.com\"}")
USER_ID=$(echo $USER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['user_id'])" 2>/dev/null)
log "Created User: $USER_ID"
check_response "$USER_RESPONSE" "user_id" "Create User"

# Create deck
DECK_RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"OS Comprehensive Test\", \"subject\": \"Operating Systems\", \"syllabus\": \"$SYLLABUS\"}")
DECK_ID=$(echo $DECK_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['deck_id'])" 2>/dev/null)
log "Created Deck: $DECK_ID"
check_response "$DECK_RESPONSE" "deck_id" "Create Deck"

# Upload material
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/upload" \
    -F "files=@/tmp/os_study_material.txt")
log "Upload Response: $UPLOAD_RESPONSE"
check_response "$UPLOAD_RESPONSE" "success" "Upload Material"

CHUNK_COUNT=$(echo $UPLOAD_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['total_chunks'])" 2>/dev/null)
log "Total Chunks Created: $CHUNK_COUNT"

sleep 2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE 1: Basic Q&A
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUITE 1: BASIC Q&A (Using /ask endpoint)"

# Test 1.1: Process States Question
log ""
log "📝 Question 1.1: What are the different process states?"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "What are the different process states in an operating system?", "pace": "medium"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "new|ready|running|waiting|terminated|blocked" "Process States Knowledge"

# Test 1.2: PCB Question
log ""
log "📝 Question 1.2: What is a Process Control Block?"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "Explain what a Process Control Block (PCB) contains", "pace": "medium"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "process id|pid|state|program counter|registers|memory" "PCB Knowledge"

# Test 1.3: Context Switching
log ""
log "📝 Question 1.3: Explain context switching"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "What is context switching and what are the steps involved?", "pace": "slow"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "save|load|state|pcb|overhead|switch" "Context Switching Knowledge"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE 2: Numerical/Calculation Questions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUITE 2: NUMERICAL QUESTIONS"

# Test 2.1: FCFS Calculation
log ""
log "📝 Question 2.1: Calculate average waiting time using FCFS"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "Calculate the average waiting time for processes P1(24ms), P2(3ms), P3(3ms) using FCFS scheduling. Show step by step.", "pace": "slow"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "17|0|24|27|average|waiting" "FCFS Calculation"

# Test 2.2: SJF Calculation
log ""
log "📝 Question 2.2: Calculate using SJF"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "For processes P1(6ms), P2(8ms), P3(7ms), P4(3ms), calculate average waiting time with non-preemptive SJF", "pace": "slow"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "7|shortest|P4|order|burst" "SJF Calculation"

# Test 2.3: Round Robin
log ""
log "📝 Question 2.3: Round Robin scheduling"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "Explain Round Robin scheduling with time quantum and its advantages", "pace": "medium"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "quantum|time|preemptive|fair|context switch" "Round Robin Knowledge"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE 3: Deadlock Questions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUITE 3: DEADLOCK QUESTIONS"

# Test 3.1: Deadlock Conditions
log ""
log "📝 Question 3.1: Four conditions for deadlock"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "What are the four necessary conditions for deadlock to occur?", "pace": "medium"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "mutual exclusion|hold and wait|no preemption|circular wait" "Deadlock Conditions"

# Test 3.2: Banker's Algorithm
log ""
log "📝 Question 3.2: Explain Banker's Algorithm"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "Explain the Bankers Algorithm for deadlock avoidance", "pace": "slow"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "available|max|allocation|need|safe|sequence" "Banker's Algorithm Knowledge"

# Test 3.3: Deadlock Prevention
log ""
log "📝 Question 3.3: Deadlock prevention strategies"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "How can we prevent deadlock? List the strategies.", "pace": "medium"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "prevent|eliminate|condition|resource|order" "Deadlock Prevention"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE 4: Memory Management
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUITE 4: MEMORY MANAGEMENT QUESTIONS"

# Test 4.1: Paging
log ""
log "📝 Question 4.1: What is paging?"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "Explain paging in memory management", "pace": "medium"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "page|frame|physical|logical|fragmentation" "Paging Knowledge"

# Test 4.2: Page Replacement - LRU vs FIFO
log ""
log "📝 Question 4.2: Compare LRU and FIFO page replacement"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "Compare LRU and FIFO page replacement algorithms", "pace": "medium"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "lru|fifo|least|first|replace|fault" "Page Replacement Knowledge"

# Test 4.3: Virtual Memory
log ""
log "📝 Question 4.3: Benefits of virtual memory"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "What are the benefits of virtual memory?", "pace": "fast"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
check_accuracy "$ANSWER" "virtual|memory|larger|process|physical|demand" "Virtual Memory Knowledge"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE 5: Domain Guard (Out-of-Scope)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUITE 5: DOMAIN GUARD (OUT-OF-SCOPE DETECTION)"

# Test 5.1: Neural Networks (off-topic)
log ""
log "📝 Question 5.1: Out-of-scope - Neural Networks"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "Explain backpropagation in neural networks", "pace": "medium"}')
IN_SCOPE=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('in_scope', True))" 2>/dev/null)
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
log "In Scope: $IN_SCOPE"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ "$IN_SCOPE" = "False" ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    log "✓ PASS: Correctly identified as OUT OF SCOPE"
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    log "✗ FAIL: Should have been flagged as out of scope"
fi

# Test 5.2: Database Normalization (off-topic)
log ""
log "📝 Question 5.2: Out-of-scope - Databases"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "What is database normalization and what are the normal forms?", "pace": "medium"}')
IN_SCOPE=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('in_scope', True))" 2>/dev/null)
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: $ANSWER"
log "In Scope: $IN_SCOPE"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ "$IN_SCOPE" = "False" ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    log "✓ PASS: Correctly identified as OUT OF SCOPE"
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    log "✗ FAIL: Should have been flagged as out of scope"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE 6: Pace Variation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUITE 6: PACE VARIATION"

# Test 6.1: Slow pace (detailed)
log ""
log "📝 Question 6.1: Slow pace - Deep explanation"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "Explain deadlocks", "pace": "slow"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
SLOW_LEN=${#ANSWER}
log "🤖 Answer Length: $SLOW_LEN characters"
log "🤖 Answer (preview): ${ANSWER:0:500}..."
check_response "$ANSWER" "deadlock" "Slow Pace Response"

# Test 6.2: Fast pace (brief)
log ""
log "📝 Question 6.2: Fast pace - Quick summary"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/ask" \
    -H "Content-Type: application/json" \
    -d '{"query": "Explain deadlocks", "pace": "fast"}')
ANSWER=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', 'ERROR'))" 2>/dev/null)
FAST_LEN=${#ANSWER}
log "🤖 Answer Length: $FAST_LEN characters"
log "🤖 Answer (preview): ${ANSWER:0:500}..."
check_response "$ANSWER" "deadlock" "Fast Pace Response"

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $SLOW_LEN -gt $FAST_LEN ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    log "✓ PASS: Slow pace ($SLOW_LEN chars) is longer than Fast pace ($FAST_LEN chars)"
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    log "⚠ NOTE: Slow pace ($SLOW_LEN) vs Fast pace ($FAST_LEN) - Length comparison"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE 7: Teaching Mode
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUITE 7: AUTO-TEACHING MODE"

# Test 7.1: Start Teaching
log ""
log "📝 Test 7.1: Starting teaching mode"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/teach/start" \
    -H "Content-Type: application/json" \
    -d '{"pace": "medium"}')
TOPIC=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('topic', 'N/A'))" 2>/dev/null)
MODE=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('mode', 'N/A'))" 2>/dev/null)
MESSAGE=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'ERROR'))" 2>/dev/null)
log "📚 Started Teaching: $TOPIC"
log "📚 Mode: $MODE"
log "📚 Lesson Preview: ${MESSAGE:0:400}..."
check_response "$RESPONSE" "topic" "Start Teaching"

# Test 7.2: Ask for simpler explanation
log ""
log "📝 Test 7.2: Chat - 'I don't understand'"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "I dont understand, can you explain it simpler?", "pace": "slow"}')
MESSAGE=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'ERROR'))" 2>/dev/null)
log "🤖 Simpler Explanation: ${MESSAGE:0:400}..."
check_accuracy "$MESSAGE" "simple|easy|basic|like|example|imagine" "Simpler Explanation"

# Test 7.3: Move to next topic
log ""
log "📝 Test 7.3: Chat - 'Next topic'"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "next topic please"}')
TOPIC=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('topic', 'N/A'))" 2>/dev/null)
PROGRESS=$(echo $RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('progress', {}).get('progress_percent', 0))" 2>/dev/null)
log "📚 New Topic: $TOPIC"
log "📚 Progress: $PROGRESS%"
check_response "$RESPONSE" "topic" "Move to Next Topic"

# Test 7.4: Ask for practice
log ""
log "📝 Test 7.4: Chat - 'Give me practice questions'"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "give me practice questions"}')
MESSAGE=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'ERROR'))" 2>/dev/null)
log "📝 Practice Questions: ${MESSAGE:0:500}..."
check_accuracy "$MESSAGE" "question|answer|practice|exercise|1|2|3" "Practice Questions"

# Test 7.5: Get teaching progress
log ""
log "📝 Test 7.5: Get teaching progress"
RESPONSE=$(curl -s "$BASE_URL/users/$USER_ID/decks/$DECK_ID/teach/progress")
log "📊 Progress: $RESPONSE"
check_response "$RESPONSE" "current_topic" "Teaching Progress"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE 8: Conversation Memory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUITE 8: CONVERSATION MEMORY"

# Exit teaching first
curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "stop teaching"}' > /dev/null

# Test 8.1: Initial question
log ""
log "📝 Test 8.1: Initial question - FCFS"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "What is FCFS scheduling?"}')
MESSAGE=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: ${MESSAGE:0:400}..."
check_accuracy "$MESSAGE" "fcfs|first|come|serve|order|arrival" "FCFS Explanation"

# Test 8.2: Follow-up question (tests memory)
log ""
log "📝 Test 8.2: Follow-up - 'What are its disadvantages?'"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "What are its disadvantages?"}')
MESSAGE=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: ${MESSAGE:0:400}..."
check_accuracy "$MESSAGE" "convoy|waiting|disadvantage|problem|long" "FCFS Disadvantages (Memory Test)"

# Test 8.3: Another follow-up
log ""
log "📝 Test 8.3: Follow-up - 'How can we solve this?'"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "How can we solve this problem?"}')
MESSAGE=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'ERROR'))" 2>/dev/null)
log "🤖 Answer: ${MESSAGE:0:400}..."
check_accuracy "$MESSAGE" "sjf|round robin|priority|scheduling|algorithm" "Solution (Memory Test)"

# Test 8.4: Get conversation history
log ""
log "📝 Test 8.4: Get conversation history"
RESPONSE=$(curl -s "$BASE_URL/users/$USER_ID/decks/$DECK_ID/history?limit=10")
TOTAL_MSGS=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null)
log "📊 Total Messages in Session: $TOTAL_MSGS"
check_response "$RESPONSE" "messages" "Conversation History"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE 9: Practice Question Generation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUITE 9: PRACTICE QUESTION GENERATION"

# Test 9.1: Practice on CPU Scheduling
log ""
log "📝 Test 9.1: Generate practice for CPU Scheduling"
RESPONSE=$(curl -s -X POST "$BASE_URL/users/$USER_ID/decks/$DECK_ID/practice" \
    -H "Content-Type: application/json" \
    -d '{"topic": "CPU Scheduling", "pace": "medium"}')
log "📝 Practice Set: $RESPONSE"
check_response "$RESPONSE" "questions" "Practice Generation"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST SUITE 10: Coverage & Deck Info
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUITE 10: DECK INFORMATION"

# Test 10.1: Get deck info
log ""
log "📝 Test 10.1: Get deck information"
RESPONSE=$(curl -s "$BASE_URL/users/$USER_ID/decks/$DECK_ID")
log "📊 Deck Info: $RESPONSE"
check_response "$RESPONSE" "syllabus_topics" "Deck Information"

# Test 10.2: Coverage check
log ""
log "📝 Test 10.2: Get coverage analysis"
RESPONSE=$(curl -s "$BASE_URL/users/$USER_ID/decks/$DECK_ID/coverage")
log "📊 Coverage: $RESPONSE"
check_response "$RESPONSE" "covered_topics" "Coverage Analysis"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Final Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

log_section "TEST SUMMARY & ACCURACY ANALYSIS"

ACCURACY=$((PASSED_TESTS * 100 / TOTAL_TESTS))

log ""
log "╔══════════════════════════════════════════════════════════════════╗"
log "║                      FINAL TEST RESULTS                          ║"
log "╠══════════════════════════════════════════════════════════════════╣"
log "║  Total Tests:      $TOTAL_TESTS"
log "║  Passed:           $PASSED_TESTS"
log "║  Failed:           $FAILED_TESTS"
log "║  Overall Accuracy: $ACCURACY%"
log "╠══════════════════════════════════════════════════════════════════╣"
log "║  User ID:  $USER_ID"
log "║  Deck ID:  $DECK_ID"
log "║  Chunks:   $CHUNK_COUNT"
log "╚══════════════════════════════════════════════════════════════════╝"
log ""

if [ $ACCURACY -ge 80 ]; then
    log "🎉 EXCELLENT! System accuracy is above 80%"
elif [ $ACCURACY -ge 60 ]; then
    log "✓ GOOD! System accuracy is acceptable"
else
    log "⚠ NEEDS IMPROVEMENT: System accuracy is below 60%"
fi

log ""
log "Test completed at: $(date '+%Y-%m-%d %H:%M:%S')"
log ""
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Full report saved to: $FINAL_LOG"
log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo -e "${GREEN}✓ Test complete! Check final.txt for full report${NC}"
