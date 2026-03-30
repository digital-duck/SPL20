# conda create -n spl2 python=3.11
# conda activate spl2

cd ~/projects/digital-duck/dd-logging
pip install -e .

cd ~/projects/digital-duck/SPL20
pip install -e .

export MOMAGRID_HUB_URL=http://192.168.0.235:9000

# sanity test
# spl run scripts/ollama_proxy.spl --adapter momagrid -m gemma3 prompt="What is 10!"

python cookbook/run_all.py --adapter momagrid --workers 10 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S)-momagrid.md  &