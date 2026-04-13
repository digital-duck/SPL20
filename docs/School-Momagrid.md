# School Momagrid — AI for Every Kid, Everywhere

> "I need neither fortune nor fame, but I need to help kids learn."

---

## The Vision

Every school in the world — from a well-funded campus in Silicon Valley to a
single-room school in rural Nigeria — deserves equal access to AI-powered
learning tools.

SPL + Momagrid makes that possible today, with hardware schools already have
or can afford, with no ongoing cloud costs, and with no student data ever
leaving the building.

---

## What a School Hub Looks Like

```
School Campus
├── Momagrid Hub  (one mini-PC in the server room)
├── Ollama        (local LLM inference — gemma4 or equivalent)
└── Students      (any device on the school network — browser-based SPL UI)
```

- One mini-PC in the server room runs the Momagrid Hub and Ollama
- Every student and teacher on campus connects to the same hub
- Workflows are shared instantly across the whole school
- No internet connection required
- No data leaves the campus
- No per-token bill — ever

---

## The Gaming PC Idea — Turning Distraction into Contribution

Many kids stay up late playing games on powerful gaming PCs. Parents worry.
Schools see it as a distraction. But that GPU is exactly what a school
Momagrid needs.

**Flip the script:**

```
Student's Gaming PC
├── school hours  → contributes GPU to School Momagrid Hub
│                  (better GPU = better models = better learning for everyone)
├── evening       → homework, build SPL workflows, create something useful
└── night         → games, earned and guilt-free
```

The gaming PC goes from "the thing that ruins my kid" to "the thing my kid
contributes to the school."

- Parents stop seeing it as a threat and start protecting it
- The student goes from feeling guilty to feeling proud
- Their RTX 4090 runs models that help hundreds of classmates every day

### The values it builds

- **Contribution over consumption** — the same machine that entertains you
  serves your community
- **Ownership** — you built something real that others depend on
- **Learning by doing** — you understand AI because you run it, not just use it

### The gamification writes itself

| Metric | What it means |
|--------|--------------|
| GPU contributed 10,000 inference calls this month | You powered your classmates' learning |
| Your workflow was used by 47 students | You built something useful |
| Top contributor in your class | Your hardware + your creativity matter |

Kids who chase leaderboards in games will chase this leaderboard too.
Except this one means something.

---

## Schools Federating into a Bigger Momagrid

Individual school hubs do not have to stand alone. Schools can peer with each
other to form a district-wide, region-wide, or even national Momagrid.

```
District Momagrid
├── School A Hub  (mini-PC + student gaming PCs)
├── School B Hub  (mini-PC + student gaming PCs)
├── School C Hub  (mini-PC + student gaming PCs)
└── ...
```

Workflow resolution follows the same federated lookup as the broader Momagrid:
local first, then peers on a miss. A workflow written by a teacher in one
school becomes available to every school in the federation — instantly, with
no central authority, no approval process, no cost.

A brilliant `grade_essay` workflow written by a teacher in Jakarta is running
in classrooms in Nairobi the same day.

---

## What This Unlocks in a School

| Who | What they build | Who benefits |
|-----|----------------|--------------|
| Student | `homework_helper` workflow | The whole class |
| Teacher | `grade_essay` workflow | Every teacher in the school |
| Librarian | `book_summarizer` workflow | All students |
| IT admin | Controls everything from one hub | The whole campus |

No student needs to know what a transformer is. No teacher needs to write
Python. They write what they want — in SPL — and the hub handles the rest.

---

## The Conversation with a Principal

A school principal does not want to hear about transformers and context
windows. They want to hear:

> "One mini-PC in your server room. Students learn AI by using it and
> building with it. No data leaves campus. No monthly bill. No vendor
> lock-in. Your students' gaming PCs contribute to it voluntarily."

That is a five-minute conversation that ends with a purchase order.

---

## The Global South Angle

A school in rural India, Indonesia, or Nigeria with one decent PC and a local
network runs the exact same setup as a well-funded school in Silicon Valley.

Same models. Same workflows. Same learning outcomes.

Zero cost. Zero cloud dependency. Zero gatekeepers.

That is what "no kids left behind" means in the AI era — not a slogan, but a
technical reality made possible by local inference and federated workflows.

---

## Why SPL Is the Right Language for This

SPL was designed with the SQL parallel in mind. SQL succeeded because it let
non-programmers express complex data operations in near-English. SPL does the
same for AI workflows.

```sql
-- A student's first AI workflow
GENERATE summarise(@article)
    USING MODEL @model
    INTO @summary
```

```sql
-- A teacher's grading assistant
CALL extract_claims(@essay) INTO @claims
CALL check_evidence(@claims) INTO @feedback
CALL grade_essay(@essay, @feedback) INTO @grade
```

The first example takes five minutes to learn. The second example — workflow
calling workflow — is something most professional AI frameworks cannot do
cleanly. A student who starts with the first naturally grows into the second.

That depth-to-accessibility ratio is what makes SPL right for education.

### The full SPL + Momagrid stack

Every layer solves a real problem. Together they form something none of the
big players have — a full stack from "kid writes a workflow" to "workflow
runs on a global federated network."

| Layer | What it is | Why it matters |
|-------|-----------|----------------|
| **SPL syntax** | SQL-like, declarative | Zero learning curve for 30M+ SQL users |
| **Local inference** | Ollama + gemma4 | Zero cost, zero cloud dependency |
| **Multimodal** | IMAGE + AUDIO native | Real-world tasks — not just text |
| **CALL composition** | Workflow calls workflow | Complexity without complexity |
| **`claude_cli` adapter** | Flat-subscription Claude access | Complex reasoning at predictable cost |
| **Momagrid** | Federated workflow registry | Workflows shared across schools and the world |
| **splc** | Compile to any target | Edge, mobile, Go, TypeScript |

---

## The Deeper Purpose

The AI era will create a new divide — between those who can direct AI and
those who can only consume it. That divide will follow existing inequality
lines unless something actively disrupts it.

SPL + Momagrid in schools is that disruption.

Not because it is charity. Because it is infrastructure — the same way
electricity, running water, and the internet became infrastructure. The goal
is a world where a kid's postal code does not determine whether they get to
participate in the AI era.

**No kids left behind.**

---

## The Cost Model — Why Schools Can Actually Afford This

### The `claude_cli` adapter changes the economics

SPL's `claude_cli` adapter routes workflow calls through the Claude CLI rather
than the Anthropic API directly. That means subscription pricing, not
per-token billing.

```
School workflow
    └── spl3 run lesson_helper.spl --adapter claude_cli
            └── Claude CLI  (flat monthly subscription)
                    └── Claude  (no per-token charge to the school)
```

One Claude subscription. Unlimited students running SPL workflows through it.
The school pays a flat monthly fee — not per inference call.

### The cost comparison

| Setup | Cost model | 1,000 student queries |
|-------|-----------|----------------------|
| OpenAI API direct | Per token | $5–$50 depending on model |
| Anthropic API direct | Per token | Similar range |
| Claude CLI adapter | Flat subscription | Same cost as 1 query |
| Ollama local | Zero | Zero |

### The hybrid strategy — best of both worlds

SPL workflows can route different tasks to different models. Simple, routine
tasks stay local at zero cost. Complex reasoning tasks use Claude via the
subscription adapter — still no per-token bill.

```sql
-- Routine tasks → local Ollama, zero cost, private
GENERATE summarise(@article)
    USING MODEL 'gemma4:e4b'
    INTO @summary

-- Complex reasoning → Claude CLI, subscription cost, no per-token charge
GENERATE analyse_essay(@essay)
    USING MODEL 'claude'
    INTO @feedback
```

The workflow decides which model handles which task. The school gets local
speed and privacy for routine work, and Claude-level reasoning for demanding
tasks — all within a predictable, flat budget.

### The conversation with a CFO

> "One Ollama mini-PC. One Claude subscription. Every student gets local AI
> for free and Claude-level reasoning for complex tasks. No per-query bill.
> No surprises at the end of the month."

That is a CFO conversation, not just a principal conversation.

### Anthropic's existing education commitment

Anthropic is already deeply invested in education:
- 1.8M+ teachers via AFT partnership
- 100,000+ educators across 63 countries via Teach For All
- Full campus access at Northeastern (50,000 students), LSE, Champlain College
- Hundreds of thousands of students in Rwanda via ALX learning companion
- Claude's dedicated "learning mode" guides reasoning rather than giving
  answers — pedagogically intentional

### SPL + Momagrid vs. Google and Anthropic education programs

SPL + Momagrid and the existing AI education programs are complementary,
not competitive — they operate at different layers.

|  | Google / Khan Academy | Anthropic | SPL + Momagrid |
|--|----------------------|-----------|----------------|
| **Model** | Cloud, subscription | Cloud, institutional | Local, zero cost |
| **Data** | Leaves campus | Leaves campus | Never leaves campus |
| **Student role** | Consumer of AI | Consumer of AI | Builder of AI |
| **Cost** | Free tier, then paid | Institutional license | Zero, forever |
| **Ownership** | Vendor's platform | Vendor's platform | School owns everything |
| **Works offline** | No | No | Yes |
| **Federated** | No | No | Yes — schools share workflows |

SPL teaches kids to *build* AI workflows; Google and Anthropic provide AI
tools to *use*. That is a fundamentally different and deeper outcome.

A post-launch partnership conversation with Anthropic's education team is a
natural next step — particularly given the Global South and
zero-cost-local-inference alignment with their stated mission.

---

## Standing on the Shoulders of Giants

Sal Khan started Khan Academy nearly twenty years ago with a simple belief:
that a world-class education should be free and available to anyone, anywhere.
It was a radical idea at the time. Today it serves hundreds of millions of
learners and has become part of the educational infrastructure of the world.

SPL + Momagrid follows that same footstep — not to compete with Khan Academy,
but to extend the same spirit into the AI era. Sal Khan gave the world free
access to knowledge. The next frontier is giving the world free access to
the tools that *create and direct* AI — not just consume it.

The goal is the same: a kid's postal code should not determine what they get
to learn, build, or become.

That is the mission. Not fortune. Not fame. Just kids — every kid — with the
tools to shape their own future.

---

*SPL and Momagrid are open-source projects. The School Momagrid initiative
is part of the broader mission to make AI accessible to everyone, everywhere,
at zero cost.*
