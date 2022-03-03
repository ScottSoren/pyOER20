"""Calculate the isotopic oxygen ratio for all samples and record
it as metadata (json)."""
import pathlib
import pyOER

handle = pyOER.ISS(verbose=False)

# Loop through all samples
for sample in handle.all_leis():
    handle.get_sample(sample)
    print(f'Handling sample: {handle.sample}')
    ratios, coeffs = handle.fit_with_reference(
        # handles all internal datasets by default
        peaks=[[16, 18]],
        region_names=['oxygen'],
        plot_result=False,
        recalculate=True,
        )
    # Save the isotope result information in JSON metadata dict
    handle.save_json()
    handle.save_extras()
