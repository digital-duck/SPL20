cd ~/projects/digital-duck/SPL20
python cookbook/run_all.py --adapter momagrid --workers 10 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S)-momagrid-4.md