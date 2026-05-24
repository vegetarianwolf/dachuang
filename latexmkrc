$do_cd = 1;
$pdf_mode = 5;
$pdflatex = 'xelatex %O %S';
$aux_dir = '.latex-build';
$out2_dir = '.';
$emulate_aux = 1;
$success_cmd = 'latexmk -silent -c %R.tex; rm -f %R.synctex.gz; rmdir .latex-build 2>/dev/null || true; (sleep 1; rm -f %R.aux %R.fdb_latexmk %R.fls %R.log %R.xdv %R.synctex.gz; rmdir .latex-build 2>/dev/null || true) &';

