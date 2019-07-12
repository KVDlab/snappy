import numpy as np
from Bio import SeqIO
import argparse
import subprocess
import pandas as pd

def splits_for_blast(target, NAME):
    """Create slices for BLAST

    This function creates multiple slices of 400 nucleotides given an fasta
    sequence. The step size is 50. This the gaps are excluded from the sequence.
    Thats why sequences with less than 400 nucleotides are excluded.

	Args:
        target (np.array): Fasta sequence in an array.
        NAME (str): Global variable. Internal index of SNAPPy for this fasta.

	Returns:
        List of fasta files slices. Each is a proper fasta.
	"""
    target_seq = target[1:]
    no_gap_t = target_seq[target_seq != '-']
    target_length = no_gap_t.shape[0]

    sub_aligns =[ [[f'>{NAME}_{x}'] , no_gap_t[x:x+400]] for x in range(0, target_length, 50) if  len(no_gap_t[x:x+400]) == 400]
    return sub_aligns


def do_sub_aligns(target, NAME):
    """Create slices for fasta file

    This function uses the output list from the function 'splits_for_blast' and
    writes  a multiple sequence alignment of several fasta file slices.
    If the original sequence (without gaps) is less than 400 nucleotide long
    the output file will contain: 'not enough genomic information'. The file is
    outputed to the folder 'blast' with the following notation:
    sub_{id_of_the_fasta_sequence}.fasta
    
	Args:
        target (fasta): Fasta file with one aligned sequence.
        NAME (str): Global variable. Internal index of SNAPPy for this fasta.

	Returns:
        This function does not return.
	"""
    seq_target = [np.array([j for j in [x.id]] + list(str(x.seq))) for x in SeqIO.parse(target, 'fasta')][0]  
    sub_alignments = splits_for_blast(seq_target, NAME)



    name_out = f'blast/sub_{NAME}.fasta'
        
    with open(name_out, 'w') as out_subs:
        for sub in sub_alignments:
            out_subs.write(f'{sub[0][0]}\n{"".join(sub[1])}\n')

    return name_out


def do_blast_window(target, NAME):
    """Do sliding window BLAST

    This function uses the fasta files created in 'do_sub_aligns' and performs a
    BLAST agains the database 'data/db_01-02_and_pures'. The BLAST results are
    written to the folder 'blast' with the following notation:
    recblast_{id_of_the_fasta_sequence}.txt

	Args:
        target (fasta): Fasta file with one aligned sequence.
        NAME (str): Global variable. Internal index of SNAPPy for this fasta.

	Returns:
        This function does not return.
	"""
    to_blast = do_sub_aligns(target, NAME)


    subprocess.call(['blastn', '-db', './data/db_01-02_and_pures', '-query',
    '{0}'.format(to_blast), '-out', 'blast/recblast_{0}.txt'.format(NAME),
    '-word_size', '30', '-outfmt', '10', '-evalue', '1.e-50'])

    df = pd.read_csv(f'blast/recblast_{NAME}.txt', header=None)
    df[[0,1,10,11]].to_csv(f'blast/recblast_{NAME}.txt', index=False)        

    comand_rm = 'rm {0}'.format(to_blast)
    subprocess.call(comand_rm.split(' '))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--input", required = True,
                            help="Name input file.")
    args = parser.parse_args()
    NAME = str(args.input).replace('aligned/aligned_' ,'').replace('.fasta', '')

    
    is_empty = str(list(SeqIO.parse(args.input, 'fasta'))[0].seq).replace('-', '')
    length = len(is_empty)

    if is_empty == '': # deal with empty fastas after alignment
        with open('blast/recblast_{0}.txt'.format(NAME), "w") as out_b:
            out_b.write('not enough genomic information\n')
    else: # process sequences normaly
        if length < 400: # unable to perform blast for seqs < 400 
            with open('blast/recblast_{0}.txt'.format(NAME), "w") as out_b:
                out_b.write('not enough genomic information\n')
        else:
            do_blast_window(args.input, NAME)
