(sleep 200; bash scripts/run_grobid.sh) &
PID=$!

python doc2json/tex2json/process_tex.py -i test_data/arXiv-2408.05159v1.tar.gz -t temp_dir_retest/ -o output_dir_retest/

kill $PID 

python json2parquent.py --data_path ./output_dir/arXiv-2408.05159v1.tar.json --tmp_path ./temp_dir 
