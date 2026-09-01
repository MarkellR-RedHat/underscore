## Underscore headless recorder for Sonic Pi 5.
##
## Usage: underscore-record.rb -o OUT.wav -d SECONDS -f FILE.rb [-s SEED]
##
## Builds on Sonic Pi's own HeadlessBoot (ships with the app) but records via
## the spider's /start-recording, /stop-recording, /save-recording commands,
## the same path the GUI's record button uses. The program must keep running
## for the whole window (the harness holds the run open), because the engine
## pauses itself when every run completes.

APP = ENV["UNDERSCORE_SONIC_PI_APP"] || "/Applications/Sonic Pi.app"
BOOT = File.join(APP, "Contents/Resources/app/server/ruby/bin/headless_boot")
require BOOT
require 'fileutils'

out = dur = file = seed = nil
args = ARGV.dup
until args.empty?
  case (f = args.shift)
  when "-o" then out  = args.shift
  when "-d" then dur  = args.shift.to_f
  when "-f" then file = args.shift
  when "-s" then seed = args.shift
  else abort "unknown argument #{f}"
  end
end
abort "need -o -d -f" unless out && dur && file && dur > 0
code = File.read(file)
code = "use_random_seed #{seed}\n" + code if seed
out = File.expand_path(out)
FileUtils.mkdir_p(File.dirname(out))

boot = SonicPi::HeadlessBoot.new.boot!
tok = boot.token
boot.say "READY recording #{dur}s -> #{out}"
boot.eval_client.send("/start-recording", tok)
sleep 0.4
boot.run(code)
sleep dur
boot.eval_client.send("/stop-recording", tok)
sleep 0.6
boot.eval_client.send("/save-recording", tok, out)
# wait for the file to land and stop growing
last = -1
20.times do
  sleep 0.5
  sz = File.exist?(out) ? File.size(out) : 0
  break if sz > 0 && sz == last
  last = sz
end
boot.stop_all
sleep 0.5
boot.say "ERRORS: #{boot.errors.join(' | ')}" unless boot.errors.empty?
if File.exist?(out) && File.size(out) > 0
  boot.say "WROTE #{out} (#{File.size(out)} bytes)"
  exit(boot.errors.empty? ? 0 : 2)
else
  boot.say "FAILED no output"
  exit 1
end
