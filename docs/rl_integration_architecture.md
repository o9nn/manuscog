# OpenManus-RL Integration Architecture

## Mapping: RL Concepts → Cognitive Kernel

| OpenManus-RL Component | Manuscog Equivalent | Integration Point |
|------------------------|--------------------|--------------------|
| Environment (base.py) | AtomSpace + World Model | `CognitiveEnvironment` wraps AtomSpace as RL env |
| Reward Manager | ECAN Attention + PLN Truth Values | `CognitiveRewardManager` uses attention/reasoning signals |
| Memory (SimpleMemory) | AtomSpace Persistence | `CognitiveMemory` backed by AtomSpace |
| GiGPO Algorithm | PLN + ECAN optimization | `CognitiveAdvantage` combines RL + cognitive signals |
| Rollout Loop | Cognitive Cycle | `CognitiveRollout` integrates think-act-reflect |
| Modular Stages | Autognosis + PLN | Planning/Action/Reflection map to cognitive subsystems |
| Tool Integration | MCP Server Tools | Cognitive tools exposed via RL action space |
| TrajectoryCollector | Autognosis Self-Monitor | Cognitive trajectory tracking |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  CognitiveRL Module                      │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Cognitive     │  │  Cognitive   │  │  Cognitive   │  │
│  │  Environment   │  │  Reward Mgr  │  │  Rollout     │  │
│  └───────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│          │                 │                  │          │
│  ┌───────┴─────────────────┴──────────────────┴───────┐  │
│  │              Cognitive RL Trainer                   │  │
│  │  (Orchestrates training with cognitive signals)     │  │
│  └────────────────────────┬──────────────────────────┘  │
│                           │                              │
├───────────────────────────┼──────────────────────────────┤
│                           │                              │
│  ┌────────────────────────┴──────────────────────────┐  │
│  │              Cognitive Kernel                      │  │
│  │  ┌──────┐ ┌─────┐ ┌──────┐ ┌──────────┐          │  │
│  │  │ PLN  │ │ECAN │ │MOSES │ │Autognosis│          │  │
│  │  └──┬───┘ └──┬──┘ └──┬───┘ └────┬─────┘          │  │
│  │     └────────┴───────┴──────────┘                 │  │
│  │              AtomSpace                             │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **AtomSpace as State Space**: Agent observations are stored as atoms;
   the state is the current AtomSpace configuration.

2. **Cognitive Rewards**: Combine environment rewards with:
   - PLN inference quality (truth value confidence)
   - ECAN attention efficiency (focus utilization)
   - Autognosis self-improvement metrics

3. **GiGPO + Cognitive Advantage**: Step-level grouping uses
   AtomSpace state fingerprints as anchor observations.

4. **Modular Stages → Cognitive Cycle**:
   Planning = PLN forward chaining
   Action = Tool execution with ECAN focus
   Reflection = Autognosis self-monitoring
   Memory = AtomSpace persistence

5. **No Heavy Dependencies**: Integration doesn't require torch/verl
   for the cognitive layer; those are optional for full RL training.
