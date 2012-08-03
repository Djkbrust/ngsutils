#!/usr/bin/env python
## category General
## desc Postprocesses a BAM file to remove all clipping from reads and alignments
## experimental
'''
Postprocesses a BAM file to remove all clipping from reads and alignments.

Hard clipping is removed from the alignment. Soft clipping is removed from
the alignment and the sequence. The number of soft clipped bases is added as
the 'ZA:i' (5' clipping) and 'ZB:i' (3' clipping) tags. The percentage of soft
clipped bases is given in the 'ZC:f' tag.
'''
import sys
import os
import pysam

bam_cigar = ['M', 'I', 'D', 'N', 'S', 'H', 'P']


def bam_removeclipping(infile, outfile):
    bam = pysam.Samfile(infile, "rb")
    out = pysam.Samfile(outfile, "wb", template=bam)
    total = 0
    count = 0
    for read in bam:
        newcigar = []
        clip_5 = 0
        clip_3 = 0

        changed = False
        if not read.is_unmapped:
            inseq = False
            for op, length in read.cigar:
                if op == 5:  # H
                    changed = True
                elif op == 4:  # S
                    changed = True
                    if not inseq:
                        clip_5 = length
                    else:
                        clip_3 = length
                else:
                    inseq = True
                    newcigar.append((op, length))

            if changed:
                read.cigar = newcigar
                orig_length = len(read.seq)

                s = read.seq
                q = read.qual

                if clip_3:
                    read.seq = s[clip_5:-clip_3]
                    read.qual = q[clip_5:-clip_3]
                else:
                    read.seq = s[clip_5:]
                    read.qual = q[clip_5:]

                newtags = list(read.tags)
                if clip_5:
                    newtags.append(('ZA', clip_5))
                if clip_3:
                    newtags.append(('ZB', clip_3))

                newtags.append(('ZC', float(clip_5 + clip_3) / orig_length))

                read.tags = newtags

                count += 1

        total += 1
        out.write(read)

    bam.close()
    out.close()
    sys.stderr.write('Wrote: %s reads\nAltered: %s\n' % (total, count))


def usage():
    print __doc__
    print """Usage: bamutils removeclipping {-f} inbamfile outbamfile

Options:
  -f     Force overwriting an existing outfile
"""
    sys.exit(-1)

if __name__ == "__main__":
    infile = None
    outfile = None
    force = False

    for arg in sys.argv[1:]:
        if arg == "-h":
            usage()
        elif arg == "-f":
            force = True
        elif not infile:
            if os.path.exists(os.path.expanduser(arg)):
                infile = os.path.expanduser(arg)
            else:
                sys.stderr.write("File: %s not found!" % arg)
                usage()
        elif not outfile:
            if force or not os.path.exists(os.path.expanduser(arg)):
                outfile = arg
            else:
                sys.stderr.write(
                    "File: %s exists! Not overwriting without -f force." % arg
                    )
                usage()
        else:
            usage()

    if not infile or not outfile:
        usage()

    bam_removeclipping(infile, outfile)
