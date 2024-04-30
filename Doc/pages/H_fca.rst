Using the FCA algorithm
=======================

Guide Steps
'''''''''''

2. **Load Molecular Data**
- Use the software's "File" menu to import the molecular
trajectory data.

3. **Access Correlation Analysis**
   - Navigate to the "Analysis" section within MDANSE.

4. **Select Correlation Function**
- Choose the specific correlation function to compute, such as
velocity autocorrelation or density autocorrelation.

5. **Configure Analysis Parameters**
- Specify the range of frames for analysis (e.g., First
Frame: 0, Last Frame: Entire trajectory, Step: 1).
   - Choose the interpolation order for precise calculations.
- Select the interpolation mode based on hardware capabilities (automatic
mode is recommended).
- Set the number of preloaded frames if using 'one-time
disk interpolation' mode to optimize memory usage (default: 50).

6. **Define Q Vectors and Atom Selection**
   - Specify the Q vectors needed for the analysis.
   - Select the relevant atom selection for the calculation.

7. **Normalization, Atom Transmutation, and Weights**
   - Specify whether normalization is required based on analysis needs.
- Set atom transmutation and weights as necessary for the
analysis.

8. **Configure Output Files and Running Mode**
   - Define the output files for storing the analysis results.
- Choose the running mode (e.g., Standard or Basic) based
on the desired output.

9. **Initiate the Calculation**
- Start the Current Correlation Function analysis by clicking on
the "Run" or "Calculate" button within the MDANSE interface.

10. **Analyze and Interpret Results**
- Review the obtained results to understand the dynamics of
density fluctuations and propagating shear modes within the molecular system effectively.

**Implementing Spectral Smoothing in MDANSE**
'''''''''''''''''''''''''''''''''''''''''''''

1. **Calculate Fourier Transforms**
- After obtaining the correlation function results using FCA, proceed
to calculate the discrete Fourier transforms of the correlation function.

2. **Apply Gaussian Window**
- Define a Gaussian window function, W(m), with adjustable parameters
(e.g., width). It is typically defined as: 
W(m) = exp(-0.5 * (α * |m| / (N_t-1))^2) for m in -(N_t-1) to N_t-1.

3. **Compute Spectral Function**
- Use the Gaussian window and the inverse transform formula
to compute the spectral function
 P_ab(n/2N_t): P_ab(n/2N_t) = Δt * Σ_{m=-(N_t-1)}^{N_t-1} exp(-2πi(nm/2N_t)) * W(m) * (1/(N-|m|)) * S_AB(m).

4. **Visualization and Analysis**
- Visualize and analyze the smoothed spectral function to gain
insights into the system's behavior in the frequency domain.



