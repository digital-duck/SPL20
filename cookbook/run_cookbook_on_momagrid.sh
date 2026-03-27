cd ~/projects/digital-duck/SPL20
export MOMAGRID_HUB_URL=http://192.168.0.184:9000
python cookbook/run_all.py --adapter momagrid --workers 5 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S)-momagrid.md