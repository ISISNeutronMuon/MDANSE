Analyzing Dynamic Coherent Structure Factor (DCSF) 
====================================================

Introduction
------------

This tutorial will guide you through the analysis of DCSF (Dynamic Coherent
Structure Factor) plots using the MDANSE software and Python. DCSF analysis
provides insights into the scattering behavior of a molecular system.

**Prerequisites**:
- MDANSE software installed.
- Basic knowledge of Python.

Access DCSF Analysis in MDANSE
-------------------------------

1. Navigate to the "Analysis" section within the MDANSE interface.
2. Select "Dynamic Coherent Structure Factor" to access the DCSF analysis.

Analysis of the Total DCSF Plot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "Total DCSF Plot" in MDANSE offers valuable insights into the scattering
behavior of your molecular system. Understanding and interpreting this plot is
essential for gaining a deeper understanding of your system's structural
characteristics and dynamic behavior.

Here are the key components and steps to analyze the Total DCSF Plot:

- **Scattering Vector (Q) Magnitude**:
  - The x-axis of the Total DCSF Plot represents the scattering vector magnitude
    (Q).
  - Scattering vector (Q) quantifies the spatial distribution of scatterers in
    your system.
  - Different Q values correspond to different structural features and scattering
    events in your system.

- **Dynamic Coherent Structure Factor (DCSF) Value**:
  - The y-axis of the Total DCSF Plot represents the DCSF value.
  - The DCSF value reflects the intensity of scattering at a specific Q value.
  - High DCSF values indicate strong scattering, while low values indicate weak
    scattering.
  - The DCSF value at a particular Q value represents the overall scattering
    contribution from all atoms or components in your system at that Q value.

- **Analyzing Peaks**:
  - Peaks in the Total DCSF Plot indicate significant scattering contributions at
    specific Q values.
  - The presence of peaks suggests the existence of structural features or
    scattering events in your system.
  - The height of a peak indicates the intensity of scattering at the
    corresponding Q value.
  - The shape and width of a peak provide additional information about the
    characteristics of the scattering event.

- **Peak Interpretation**:
  - Broad Peaks: Broad peaks in the Total DCSF Plot may suggest diffusive motion
    within your system. These motions can indicate disordered or liquid-like
    regions.
  - Sharp Peaks: Sharp and well-defined peaks suggest ordered structures or
    scattering events with distinct spatial arrangements of atoms or components.

- **Comparative Analysis**:
  - Compare the Total DCSF Plot with other experimental data or simulations to
    validate your findings and gain a deeper understanding of your system's
    behavior.
  - Consider how changes in system parameters or conditions impact the DCSF plot.
    For example, compare different simulation trajectories or conditions to
    observe variations in scattering behavior.

To assist in your analysis, here's a Python code snippet that demonstrates how to
analyze the Total DCSF Plot:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# Replace with your actual data
q_values_total = np.linspace(0, 10, 100)
dcsf_values_total = np.sin(q_values_total) + np.random.normal(0, 0.2, 100)

# Analyze the Total DCSF Plot
peak_indices_total, peak_heights_total = find_peaks(dcsf_values_total,
                                                    height=0.5)

# Print peak information for Total DCSF Plot
print("Total DCSF Peaks:")
for i, idx in enumerate(peak_indices_total):
    print(f"Peak {i + 1}: Q = {q_values_total[idx]:.2f}, Height = {peak_heights_total[i]:.2f}")

# Plot Total DCSF with peaks
plt.figure(figsize=(10, 6))
plt.plot(q_values_total, dcsf_values_total, label="Total DCSF")
plt.scatter(q_values_total[peak_indices_total], peak_heights_total, color='red', marker='x', label='Peaks')
plt.xlabel("Scattering Vector (Q)")
plt.ylabel("DCSF Value")
plt.title("Total DCSF Plot with Peaks")
plt.legend()
plt.grid(True)
plt.show()


Analysis of the Partial DCSF Plot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once you've selected the relevant atom type or group for your Partial Dynamic Coherent
Structure Factor (DCSF) analysis, a partial DCSF plot specific to that selection will be
displayed. Analyzing this plot is essential for gaining insights into the scattering behavior
of the chosen component. Here's how to analyze the Partial DCSF Plot effectively:

- **Scattering Intensity**:
  - Examine the intensity of scattering at different Q values (scattering vectors) within the
    partial DCSF plot.
  - Peaks in the partial DCSF plot indicate significant scattering contributions from the
    selected atoms or group.
  - High peak values indicate pronounced scattering at specific Q values, signifying structural
    features or dynamic events associated with the chosen component.

- **Peak Characteristics**:
  - Evaluate the height, shape, and width of the peaks in the partial DCSF plot.
  - These peak characteristics provide valuable insights into the scattering behavior of the
    selected component.
  - Height: The peak height reflects the intensity of scattering at the corresponding Q value.
    Higher peaks indicate more intense scattering events.
  - Shape and Width: The shape and width of peaks offer information about the nature of
    scattering events. Broad peaks may suggest diffusive motion, while sharp, well-defined
    peaks indicate ordered structures or distinct scattering events.

- **Interactions and Correlations**:
  - Consider any interactions or correlations between the selected atoms or groups within your
    molecular system.
  - Peaks in the partial DCSF plot can reveal how these components scatter X-rays or neutrons,
    providing insights into structural features or dynamic motions.
  - Identify scattering events that may result from interactions between the chosen component
    and its surroundings.

- **Comparative Analysis**:
  - To better understand the relative contributions of different components to the overall
    scattering pattern, compare the partial DCSF plot for the selected component with the Total
    DCSF Plot.
  - This comparison allows you to assess how the scattering behavior of the chosen component
    influences the overall system scattering.

By following these guidelines and considering scattering intensity, peak characteristics,
interactions, and comparisons, you can thoroughly analyze the Partial DCSF Plot. This analysis
helps you uncover valuable information about the scattering behavior and contributions of the
selected atom type or group within your molecular system.



.. code-block:: python

    import numpy as np
    import matplotlib.pyplot as plt
    from scipy.signal import find_peaks

    # Replace with your actual data
    q_values_partial = np.linspace(0, 10, 100)
    dcsf_values_partial = np.cos(q_values_partial) + np.random.normal(0, 0.2, 100)

    # Analyze the Partial DCSF Plot
    peak_indices_partial, peak_heights_partial = find_peaks(dcsf_values_partial, height=0.5)

    # Print peak information for Partial DCSF Plot
    print("\nPartial DCSF Peaks:")
    for i, idx in enumerate(peak_indices_partial):
        print(f"Peak {i + 1}: Q = {q_values_partial[idx]:.2f}, Height = {peak_heights_partial[i]:.2f}")

    # Plot Partial DCSF with peaks
    plt.figure(figsize=(10, 6))
    plt.plot(q_values_partial, dcsf_values_partial, label="Partial DCSF")
    plt.scatter(q_values_partial[peak_indices_partial], peak_heights_partial, color='red', marker='x', label='Peaks')
    plt.xlabel("Scattering Vector (Q)")
    plt.ylabel("DCSF Value")
    plt.title("Partial DCSF Plot with Peaks")
    plt.legend()
    plt.grid(True)
    plt.show()#


Conclusion
----------

This tutorial has shown you how to access and analyze Dynamic Coherent Structure Factor (DCSF)
plots in MDANSE and perform peak analysis using Python. DCSF analysis provides valuable insights
into the scattering behavior of molecular systems, allowing you to understand structural features
and motions.

