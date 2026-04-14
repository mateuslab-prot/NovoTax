# Example run

## Data

The following example contains all the commands to run a subset of the analysis performed in the paper. They were chosen to be representative of the different datatypes (DDA / DIA) and different findings. It consists of five files:
* **Biodiversity_C_Baltica_T240_R3_Inf_27Jan16_Arwen_15-07-13.mgf** - From [PXD010000](https://www.ebi.ac.uk/pride/archive/projects/PXD010000), DDA data with no detected contamination
* **Biodiversity_HL93_HLHfructose_aerobic_3_09Jun16_Pippin_16-03-39.mgf** - From [PXD010000](https://www.ebi.ac.uk/pride/archive/projects/), DDA data with two species detected (one probable contamination)
* **Biodiversity_P_ruminicola_MDM_anaerobic_1_09Jun16_Pippin_16-03-39.mgf** - From [PXD010000](https://www.ebi.ac.uk/pride/archive/projects/), DDA data with multiple species detected as probable contamination 
* **20181112_QX8_PhGe_SA_EasyLC12-14_B_a8_221_TP96hrs_control_rep1.mzML** & **20181112_QX8_PhGe_SA_EasyLC12-12_B_a6_222_TP96hrs_control_rep2.mzML** - From [PXD036445](https://www.ebi.ac.uk/pride/archive/projects/PXD036445), DIA data from complex community. Highlights using multiple files from one experiment.

These files are [deposited to Zenodo](https://zenodo.org/records/19495971) and will be downloaded when running the example script.

## Running the example
First, please [verify that the environment is working correctly](installation.md#3-verify-the-environment-with-gpu-support) and [that the databases are setup](installation.md#4-setting-up-novotax).

To run the example a convenience script is provided that:
* Downloads the files [listed above](#data)
* Performs the full NovoTax pipeline
    * De novo prediction of peptides
    * Database matching against GTDB

A guide showing the expected output and analysis of this is also included below.

## Expected output

