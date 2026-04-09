---
layout: default # Tells Jekyll to wrap this content with _layouts/default.html
title: Run SCAM nudging # Shows up as the text in the browser tab
---

### Create Nudged IOP forcing using CAM for use with SCAM

This procedure will generate IOP forcing data associated with the dates and area of the SOCRATES field campaign to use with SCAM.

* The first experiment will provide initial conditions that approximates the state of the atmosphere at daily time intervals throughout the period of the SOCRATES field campaign.  The ERA5 reanalysis data will be used to nudge the thermodynamic vertical profiles via the T,U,V and Q fields for the initial CAM run.
* The second experiment will also be a full 3d cam run which uses the initial condition/restart boundary data along with the CAMIOP and windowing capability of the nudging functionality to generate CAM IOP forcing that can be used with SCAM to rerun the state of any individual column.
* The third experiment runs the single column version of CAM using the initial condition data along with the IOP forcing to rerun a specific column of the atmosphere during the SOCRATES period.

The output of the SCAM run can be compared to the same column of the initial CAM run to see how the model atmosphere evolves (away?) from the nudged (observed) atmospheric state.  Many SCAM runs can be made to analyze the physics processes and modify the parameterizations to help improve the prognosed state.

There are three scripts for making these runs under the SCAM_scripts directory:
* First: CAM6 run to create a ground truth dataset that is nudged to ERA5 reanalysis
```tcsh
SCAM_scripts/create_CAM6_ne30_Global_Nudged_SOCRATES_Jan-Feb_2018
```
* Second: CAM6 run(s) to generate CAM IOP data. CAM will nudge to ERA5 reanalysis outside the SOCRATES area
```tcsh
SCAM_scripts/create_CAM6_ne30_Window_Nudged_SOCRATES_CAMIOP_Jan-15-16_RF01
```
* Third: single column atmosphere (SCAM) run(s) using the generated CAM IOP data.
```tcsh
SCAM_scripts/create_CAM6_ne30_SCAM_RUN
```

The steps outlined below place the CAM code and COMPASS-cookbook underneath your $HOME directory.  The 3 CAM/SCAM cases that are created from the cookbook scripts are located under your scratch space on Derecho.  The CAM experiments will generated a terabyte of data which can be handled by $SCRATCH.  These initial cases are writing out a lot of data for analysis as we are fine tuning our procedures. The final requirements will be much less. Since the SCAM experiment is just a single column it always puts out much smaller data sets and can be easily run on any filesystem.

Before you begin, you may find it useful to review the [SCAM Tips]({{ site.baseurl }}/scam_tips/) page.

#### Configure your work area

1. Create the collections and cases directories and check out your own version of the CAM code.
```tcsh
> mkdir -p $SCRATCH/cases
> mkdir -p $HOME/collections
> mkdir -p $HOME/cases
> cd $HOME/collections
> git clone https://github.com/jtruesdal/CAM-1 CAM_6_4_120_compass
> cd CAM_6_4_120_compass
> git checkout compass
> ./bin/git-fleximod update
```
1. If you haven't already, checkout the COMPASS cookbook repository and navigate to the SCAM_scripts dir.
```tcsh
> cd $HOME/collections
> git clone https://github.com/NCAR/INFORM-COMPASS-cookbook.git
> cd INFORM-COMPASS-cookbook/SCAM_scripts
```

1. If you changed the location of the code or case directories, edit the CESMDIR, CASEDIR, and DATADIR variables in the following script to point to your new locations.
```tcsh
> vi create_CAM6_ne30_Global_Nudged_SOCRATES_Jan-Feb_2018
> vi create_CAM6_ne30_Window_Nudged_SOCRATES_CAMIOP_Jan-15-16_RF01
> vi create_CAM6_ne30_SCAM_RUN
```
1. You can also change the start date, number of days to run, and how to break up the runs under `### Run Configuration`.

1. The case title is set in the scripts using a combination of the model resolution, compset and other specifics about the experiment.  If you would like to rename the case for this experiment then edit the following line to set CASENAME as you wish.  The script will stop if you try to overwrite a previous case.
```tcsh
 set CASENAME=${CASETITLE}.${COMPSET}.${RES}.${CASEID}.${EXP}
```

1. If you have not already, you will need to set a PBS_ACCOUNT environment variable in your $HOME/.tcshrc file to provide your project number.
```tcsh
> vi ~/.tcshrc
  > setenv PBS_ACCOUNT "P########"
> source ~/.tcshrc (just needed the first time, will be run automatically each time you login in the future)
```

#### Run the first globally nudged experiment

```tcsh
> cd $HOME/collections/INFORM-COMPASS-cookbook/SCAM_scripts
> qcmd -- ./create_CAM6_ne30_Global_Nudged_SOCRATES_Jan-Feb_2018
```
You can check the status of the run, or delete it, using the scam commands described on the [Configure Scam]({{ site.baseurl }}/scam/) page.

 * After the first experiment finishes, you should have output data underneath $SCRATCH/cases/your_case_name/run.  See what you have!
```tcsh
> cd /glade/derecho/scratch/$USER/cases/f.e30.cam6_4_120.FHIST_BGC.ne30_ne30_mg17.SOCRATES_nudgeUVTQsoc_full_withCOSP_tau6h_2months_inithist.100.cosp/run
> ls -al *.cam.h*
```

#### Run the second experiment

1. Set up the second experiment to generate the IOP data for the SCAM run.
*  Modify the following script variables to specify the dates that you want to generate IOP data for. As an example the following variables are set for the first SOCRATES flight RF01 that began Jan 15 2018.
```tcsh
set RUN_STARTDATE=2018-01-15
set RUN_REFDATE=2018-01-15
set EXP=rf01.cosp
set STOP_OPTION=ndays
set STOP_N=3
set REST_OPTION=${STOP_OPTION}
set REST_N=${STOP_N}
set RUN_REFCASE=f.e30.cam6_4_120.FHIST_BGC.ne30_ne30_mg17.SOCRATES_nudgeUVTQsoc_full_withCOSP_tau6h_2months_inithist.100.cosp
set RUN_REFDIR=/glade/derecho/scratch/$USER/cases/${RUN_REFCASE}/run
set GET_REFCASE=TRUE
```
You also might want to change the filename to reflect the new flight number and date.

1. Run the second experiment to generate IOP data for SCAM.
```tcsh
> cd $HOME/collections/INFORM-COMPASS-cookbook/SCAM_scripts
> qcmd -- ./create_CAM6_ne30_Window_Nudged_SOCRATES_CAMIOP_<flight designation>
```

1. See what the second experiment generated
```tcsh
> cd /glade/derecho/scratch/$USER/cases/f.e30.cam6_4_120.FHIST_BGC.ne30_ne30_mg17.SOCRATES_nudgeUVTQwindow_withCOSP_tau6h_3days_camiop.<flight>.cosp/run
```

#### Run the third experiment, the SCAM run
1. Set up for the third experiment. SCAM will accept a global IOP file and use namelist variables to extract the correct column inline. The `*h1i*nc` IOP files from the second run contain the variables that SCAM needs (Ps, u, v, etc.)
   * Copy the IOP file from exp 2 for the correct dates to $SCRATCH
For example, RF01 takes off on Jan 15 and lands on Jan 16 so concatenate those two days to an RF01 iopfile using ncrcat. Change the dates and flights as needed below.
   ```tcsh
   > module load nco (if you haven't already)
   > ncrcat /glade/derecho/scratch/$USER/cases/f.e30.cam6_4_120.FHIST_BGC.ne30_ne30_mg17.SOCRATES_nudgeUVTQwindow_withCOSP_tau6h_3days_camiop.<flight>.cosp/run/f.e*window*h1i*2018-01-1[56]*nc /glade/derecho/scratch/$USER/<flight>.IOP.nc
   ```
   You can cat as many dates as you like; at some point the IOP file size will be the limitation. At that point you might subset each of the files to just include the lat/lon of interest of perhaps just the SOCRATES region and then cat those together.
For example if you know the index of the column you need (correct lat/lon) then you could extract that column and concatenate all of january using:
   ```tcsh
   ncrcat -d ncol,32326 -d ncol_d,32326 ...
   ```
   * modify create_CAM6_ne30_SCAM_RUN script to set REFCASE variables, paths, and dates as done for the second experiment.
   * set PTS_LAT and PTS_LON variables in the script to point to the column you would like to simulate. The PTS_LAT and PTS_LON should point to a column in SOCRATES area.
   ```tcsh
   > cd $HOME/collections/INFORM-COMPASS-cookbook/SCAM_scripts
   > emacs create_CAM6_ne30_SCAM_RUN
   ```
   * modify the following line to point to your iop file
   ```tcsh
   iopfile = '/glade/derecho/scratch/$USER/<flight>.IOP.nc'
   ```
   * modify PTS_LAT and PTS_LON to point to the column you want to simulate. To find a lat/lon along the flight track for this flight, visit the [SOCRATES catalog maps](http://catalog.eol.ucar.edu/maps/socrates) and use the playback functionality to set the Date / Time to the end of the flight. Click on a wind barb on the flight track to see the lat/lon at that location. The following is a lat/lon from the return leg where it doglegs to the left.
   ```tcsh
   set PTS_LON=152.658997
   set PTS_LAT=-54.957001
   ```

1. Run SCAM
```tcsh
> cd $HOME/collections/INFORM-COMPASS-cookbook/SCAM_scripts
> qcmd -- ./create_CAM6_ne30_SCAM_RUN
```

1. See what the third experiment generated
   * Confirm the run completed
   ```tcsh
   > cd /glade/derecho/scratch/$USER/cases/f.e30.cam6_4_120.FHIST_BGC.ne30_ne30_mg17.SOCRATES_3days_scam.<flight>.cosp/run
   > ls -rt
   > zcat <last_atm_file> | tail -10
   ```
   You will see ******* END OF MODEL RUN ******* if the run completed successfully, or an error.
   * The *h0i* and *h1i* files are the final data. View them with ncview
   ```tcsh
   > module add ncview
   > ncview <h0i_file>
   ```

#### Next steps

These experiments should be analyzed and improved through several iterations.  Some items for consideration:
* How long a spin up is needed to bring the CAM into a quasi equilibrated state for the SOCRATES start dates?  Our first run started 2 weeks before SOCRATES start.
* What model variables should be nudged and what nudging parameters work best to achieve a state that is close to the obs but not too far from CAM equilibrium
  -  Exp. 1 and 2 used 6 hour nudging on T,U,V, and Q. Should we just be nudging with T,U, and V? Is a 6hr Tau nudge timescale too strong?  Do we need to nudge hourly?
  -  Exp. 1 is a global nudge to bring the SOCRATES area close to the reanalysis state
  -  Exp. 2 is nudged outside the SOCRATES region using the windowing feature of CAM nudging to allow the physics parameterizations in the SOCRATES area to evolve freely
* How long is the observed state maintained inside the windowed area during the SOCRATES period?
  -  Do we need to use initial nudged IC data before each flight?  How quickly does the model initial state degrade for the various observed weather regimes?
* SCAM only works with boundary data on the dynamics grid.  The physics grid can't be used.  I interpolated Isla's ne30pg3 ERA forcing to the ne30np4 grid but it might be better to have Isla regenerate the forcing data for the ne30np4 grid directly.
* How close is the nudged CAM state to the ERA reanalysis?
