# Underscore render: deep-dive-amin-60s-1109
use_bpm 84
use_random_seed 1109
use_debug false

# ---------------- generated palette + sections ----------------
# ============================================================
# Collection: glass  |  A minor, 84 bpm  |  cinematic ambient
# Palette + section/hit definitions only. Harness sequences.
# ============================================================

# ---------- harmony ----------
# i - VI - III - VII with add9 / sus2 voicings, wide spacing.
define :us_prog do
  [[:a4, :madd9, :a2], [:f4, :add9, :f2], [:c4, :add9, :c3], [:g4, :sus2, :g2]]
end

define :us_prog_root do
  [[:a4, :madd9, :a2], [:a4, :sus2, :a2], [:a4, :madd9, :a2], [:a4, :madd9, :a2]]
end

# lead notes an octave above the pad voicing (all > midi 72)
define :us_lead_notes do |root, kind|
  chord(root, kind).map { |n| n + 12 }
end

# ---------- voices ----------
define :us_pad do |root, kind, amp_v, len|
  with_synth :blade do
    play chord(root, kind), attack: len * 0.35, sustain: len * 0.25,
         release: len * 0.6, amp: amp_v, cutoff: 100
  end
end

define :us_pad_bright do |root, kind, amp_v, len|
  with_synth :blade do
    play chord(root, kind), attack: len * 0.3, sustain: len * 0.3,
         release: len * 0.6, amp: amp_v, cutoff: 110
    play chord(root, kind).max + 12, attack: len * 0.4, sustain: len * 0.2,
         release: len * 0.6, amp: amp_v * 0.5, cutoff: 110
  end
end

define :us_bass do |n, amp_v, len|
  with_synth :fm do
    play n, depth: 1.5, divisor: 2, attack: 0.02,
         sustain: len * 0.5, release: len * 0.5, amp: amp_v
  end
end

define :us_pluck do |n, amp_v|
  with_synth :pluck do
    play n, attack: 0, release: 0.9, amp: amp_v, coef: 0.3
  end
end

define :us_tick do |amp_v|
  sample :elec_tick, amp: amp_v, rate: 1.2
end

define :us_kick do |amp_v|
  sample :bd_haus, amp: amp_v, rate: 1.0
end

define :us_bell do |amp_v|
  sample :elec_blip, amp: amp_v, rate: 1.5
end

# ---------- hits ----------
define :hit_riser do
  in_thread do
    with_fx :reverb, room: 0.8, mix: 0.3 do
      with_synth :blade do
        s = play :a4, note_slide: 3.5, attack: 0.5, sustain: 3,
                 release: 0.5, amp: 0.22, cutoff: 100
        control s, note: :a5
      end
      scale(:a5, :minor, num_octaves: 1).each do |n|
        us_pluck n, 0.22
        sleep 0.5
      end
    end
  end
end

define :hit_soft_hit do
  in_thread do
    with_fx :reverb, room: 0.8, mix: 0.3 do
      sample :bd_pure, amp: 0.4
      with_synth :pretty_bell do
        play chord(:a5, :sus2), attack: 0.01, release: 2, amp: 0.25
      end
    end
  end
end

# ---------- sections ----------

# sec_0: calm, energy 0.40 — pad, bass pulse on 1 & 3, offbeat ticks,
# sparse eighth arp from bar one. No kick.
define :sec_0 do |bars|
  pat = [0, 1, nil, 2, nil, 3, 2, nil]
  with_fx :hpf, cutoff: 30 do
    with_fx :reverb, room: 0.8, mix: 0.3 do
      bars.times do |bar|
        root, kind, bn = us_prog()[bar % 4]
        arp = us_lead_notes(root, kind)
        us_pad root, kind, 0.3, 4
        8.times do |i|
          us_bass bn, 0.3, 2 if i == 0 || i == 4
          us_tick 0.12 if i.odd?
          idx = pat[i]
          us_pluck arp[idx % arp.length], 0.28 if idx
          sleep 0.5
        end
      end
    end
  end
end

# sec_1: serious, energy 0.50 — adds a single kick on beat 1,
# full eighth arp, steady ticks.
define :sec_1 do |bars|
  pat = [0, 1, 2, 3, 2, 1, 3, 0]
  with_fx :hpf, cutoff: 30 do
    with_fx :reverb, room: 0.8, mix: 0.3 do
      bars.times do |bar|
        root, kind, bn = us_prog()[bar % 4]
        arp = us_lead_notes(root, kind)
        us_pad root, kind, 0.32, 4
        8.times do |i|
          us_kick 0.4 if i == 0
          us_bass bn, 0.32, 2 if i == 0 || i == 4
          us_tick(i.even? ? 0.1 : 0.14)
          us_pluck arp[pat[i] % arp.length], 0.3
          sleep 0.5
        end
      end
    end
  end
end

# sec_2: lift, energy 0.70 — kick on 1 and 3, brighter pad with an
# upper voice, bell accents on offbeats, bass on every beat.
define :sec_2 do |bars|
  pat = [0, 2, 1, 3, 0, 3, 2, 1]
  with_fx :hpf, cutoff: 30 do
    with_fx :reverb, room: 0.85, mix: 0.3 do
      bars.times do |bar|
        root, kind, bn = us_prog()[bar % 4]
        arp = us_lead_notes(root, kind)
        us_pad_bright root, kind, 0.34, 4
        8.times do |i|
          us_kick 0.42 if i == 0 || i == 4
          us_bass bn, 0.32, 1 if i.even?
          us_tick(i.even? ? 0.1 : 0.15)
          us_bell 0.18 if i == 3 || (i == 7 && bar.odd?)
          us_pluck arp[pat[i] % arp.length], 0.32
          sleep 0.5
        end
      end
    end
  end
end

# sec_3: resolve, energy 0.30 — root chord only, one bass note,
# quiet quarter-note arp on bar 1, pad alone on the last bar.
define :sec_3 do |bars|
  with_fx :hpf, cutoff: 30 do
    with_fx :reverb, room: 0.85, mix: 0.3 do
      bars.times do |bar|
        last = (bar == bars - 1)
        root, kind, bn = us_prog_root()[bar % 4]
        arp = us_lead_notes(root, kind)
        us_pad root, kind, (last ? 0.22 : 0.3), 4
        us_bass bn, 0.28, 4 if bar == 0
        us_bell 0.15 if last
        8.times do |i|
          us_pluck arp[(i / 2) % arp.length], 0.2 if !last && i.even?
          sleep 0.5
        end
      end
    end
  end
end

# ---------------- harness (sequencing, do not edit) ----------------
in_thread do
  sleep 59.9998
  hit_riser
end
in_thread do
  sleep 76.0004
  hit_soft_hit
end
sec_0 5
sec_1 10
sec_2 4
sec_3 2
sleep 19.6000  # hold for the recorder tail
