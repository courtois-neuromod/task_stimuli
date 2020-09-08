

def write_cut_script(
        movie_file, cuts, segment_name, output_file, framerate=24000/1001.,
        overlap = 4,
        fade_in=2, fade_out=2, black_screen_end=4,
	crop_top_bar=140, crop_bottom_bar=140):


	f=open(output_file, 'w')
	for seg,sta,sto in zip(range(1,len(cuts)),cuts[:-1],cuts[1:]):
	        output_seg_fname = segment_name%seg
	        f.write("""
singularity run \
-B $PWD:/input \
-B $PWD:/output \
/mnt/data_sq/neuromod/CONTAINERS/melt.simg \
-silent \
colour:black out=%d \
%s in=%d out=%d -attach-clip crop left=0 right=0 top=%d bottom=%d -mix %d -mixer luma \
colour:black out=%d -mix %d -mixer luma \
-attach-track ladspa.1403 0=-25 1=0.25 2=0.4 3=0.6 \
-attach-track ladspa.1913 0=17 1=-3 2=0.5 \
-attach-track volume:-70db end=0db in=0 out=%d \
-attach-track volume:0db end=-70db in=%d out=%d \
-consumer avformat:%s f=matroska acodec=libmp3lame ab=256k vcodec=libx264 b=5000k
"""%(int(fade_in*framerate)-1, # duration of fade_in from black
     movie_file, int(round(sta*framerate)), int(round((sto+overlap)*framerate)), crop_top_bar, crop_bottom_bar, int(fade_in*framerate), # segment start stop, crop and fade_in mix
     int((fade_out+black_screen_end)*framerate),int(fade_out*framerate)-1, # fade_out and black screen
     int(fade_in*framerate),int((sto-sta-fade_out)*framerate),sto-sta, # sound fade-in and fade-out
     output_seg_fname))

        f.close()


def parse_args():
        import argparse
        parser = argparse.ArgumentParser(
                prog='main.py',
                description=('Write a shell script to cut a movie'),
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--input', '-i',
                            help='Movie input file')
        parser.add_argument('--cuts', '-c', nargs='+',
                            help='cuts position in seconds')
        parser.add_argument('--segment_name', '-s',
                            help='Segment file name (must include %02d)')
        parser.add_argument('--output', '-o',
                            help='the output script filename')
        #parser.add_argument('--framerate', '-f',
        #                    help='framerate')

        return parser.parse_args()
            
if __name__ == "__main__":
       parsed = parse_args()

       write_cut_script(
               parsed.input,
               [int(c) for c in parsed.cuts],
               parsed.segment_name,
               parsed.output)
