"""Calculate the isotopic oxygen ratio for all samples and record
it as metadata (json)."""
import pathlib
import pyOER

handle = pyOER.ISS()

# Loop through all samples
all_samples = [sample.stem for sample in handle.json_path.rglob('*.json')]
all_samples.sort()
for sample in all_samples:
    handle.get_sample(sample)
    ratios, coeffs = handle.fit_with_reference(
        peaks=[[16, 18]],
        plot_result=False,
        verbose=False,
        )

    # Save the isotope result information in JSON metadata dict
    for data in handle:
        key = handle.active
        if ratios[key]:
            results = {
                'O16': ratios[key]['16']*100,
                'O18': ratios[key]['18']*100,
                'c_16': coeffs[key][16],
                'c_18': coeffs[key][18],
                }
        else:
            results = {
                'O16': None,
                'O18': None,
                'c_16': None,
                'c_18': None,
                }
        handle.update_meta('results', results)
    handle.save_json()

