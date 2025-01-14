wolframscript -c 'Export["/tmp/plot.pdf", ListLinePlot[Association@Import["http://cobalt:1111/get_history", "JSON"], PlotRange -> Full, LabelStyle -> {FontColor -> White}, Ticks -> {None, Automatic}, AxesStyle -> White]];'
imgcat /tmp/plot.pdf
rm /tmp/plot.pdf