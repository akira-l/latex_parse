(sleep 200; bash scripts/run_grobid.sh) &
PID=$!

python doc2json/tex2json/process_tex.py -i test_data/arXiv-2408.05159v1.tar.gz -t temp_dir_arXiv-2408.05159v1.tar.gz/ -o output_dir/

python json2parquent.py --data_path ./output_dir/arXiv-2408.05159v1.tar.json --tmp_path ./temp_dir_arXiv-2408.05159v1.tar.gz 

python json2md.py --data_path ./output_dir/arXiv-2408.05159v1.tar.json --tmp_path ./temp_dir_arXiv-2408.05159v1.tar.gz 

mv arXiv-2408.05159v1.md ./output_dir

python doc2json/tex2json/process_tex.py -i test_data/arXiv-2408.06072v1.tar.gz -t temp_dir_arXiv-2408.06072v1.tar.gz/ -o output_dir/

python json2parquent.py --data_path ./output_dir/arXiv-2408.06072v1.tar.json --tmp_path ./temp_dir_arXiv-2408.06072v1.tar.gz 

mv arXiv-2408.05159v1.md ./output_dir

kill $PID 


