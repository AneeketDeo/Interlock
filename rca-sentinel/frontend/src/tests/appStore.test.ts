import { describe, it, expect, beforeEach } from 'vitest';
import { useAppStore } from '../state/useAppStore';

describe('AppStore & Scenario State Machine', () => {
  beforeEach(() => {
    useAppStore.getState().resetScenario();
  });

  it('initializes with nominal status at stage 0', () => {
    const state = useAppStore.getState();
    expect(state.timelineStage).toBe(0);
    const line03 = state.lines.find((l) => l.id === 'line-03');
    const station03b = state.stations.find((s) => s.id === 'st-03b');
    expect(line03?.status).toBe('nominal');
    expect(station03b?.status).toBe('nominal');
    expect(station03b?.scrapRate).toBe(0.8);
  });

  it('triggers anomaly spike when stepping to stage 1', () => {
    useAppStore.getState().setTimelineStage(1);
    const state = useAppStore.getState();
    expect(state.timelineStage).toBe(1);

    const line03 = state.lines.find((l) => l.id === 'line-03');
    const station03b = state.stations.find((s) => s.id === 'st-03b');
    expect(line03?.scrapRate).toBe(12.2);
    expect(line03?.status).toBe('degraded');
    expect(station03b?.status).toBe('critical');
    expect(station03b?.vibrationMmS).toBe(4.82);
  });

  it('executes interlock containment when reaching stage 7', () => {
    useAppStore.getState().setTimelineStage(7);
    const state = useAppStore.getState();
    expect(state.timelineStage).toBe(7);

    const line03 = state.lines.find((l) => l.id === 'line-03');
    const station03b = state.stations.find((s) => s.id === 'st-03b');
    expect(line03?.status).toBe('halted');
    expect(station03b?.status).toBe('interlocked');
    expect(station03b?.vibrationMmS).toBe(0.0);
  });

  it('handles stepping forward and backward bounded between 0 and 7', () => {
    useAppStore.getState().stepBackward(); // Should not go below 0
    expect(useAppStore.getState().timelineStage).toBe(0);

    useAppStore.getState().stepForward();
    expect(useAppStore.getState().timelineStage).toBe(1);

    useAppStore.getState().setTimelineStage(7);
    useAppStore.getState().stepForward(); // Should not exceed 7
    expect(useAppStore.getState().timelineStage).toBe(7);
  });

  it('allows human engineer to approve proposals and triggers containment', () => {
    const proposals = useAppStore.getState().proposals;
    expect(proposals.length).toBeGreaterThan(0);

    const p1 = proposals[0].id;
    const p2 = proposals[1].id;

    useAppStore.getState().approveProposal(p1, 'Chief Engineer Sarah Connor');
    let updated = useAppStore.getState().proposals.find((p) => p.id === p1);
    expect(updated?.status).toBe('approved');
    expect(updated?.signedBy).toBe('Chief Engineer Sarah Connor');

    // Second approval triggers stage 7 containment
    useAppStore.getState().approveProposal(p2, 'Chief Engineer Sarah Connor');
    expect(useAppStore.getState().timelineStage).toBe(7);
  });

  it('supports proposal rollback', () => {
    const p1 = useAppStore.getState().proposals[0].id;
    useAppStore.getState().approveProposal(p1);
    useAppStore.getState().rollbackProposal(p1);

    const updated = useAppStore.getState().proposals.find((p) => p.id === p1);
    expect(updated?.status).toBe('rolled_back');
  });

  it('toggles theme between night and day', () => {
    useAppStore.getState().setTheme('night');
    expect(useAppStore.getState().theme).toBe('night');

    useAppStore.getState().toggleTheme();
    expect(useAppStore.getState().theme).toBe('day');

    useAppStore.getState().toggleTheme();
    expect(useAppStore.getState().theme).toBe('night');
  });
});
