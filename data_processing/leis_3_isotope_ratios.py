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
    print(f'Handling sample: {handle.sample}')
    # Save the isotope result information in JSON metadata dict
    for data in handle:
        results = {
            'O16': dict(),
            'O18': dict(),
            'c_16': dict(),
            'c_18': dict(),
            }
        key = handle.active
        print(f'Datafile {key}')
        for i in data:
            print(f'Internal dataset {i}')
            ratios, coeffs = handle.fit_with_reference(
                selection=[key],
                peaks=[[16, 18]],
                plot_result=False,
                )
            if ratios[key]:
                results['O16'][i] = ratios[key]['16']*100
                results['O18'][i] = ratios[key]['18']*100
                results['c_16'][i] = coeffs[key][16]
                results['c_18'][i] = coeffs[key][18]
            else:
                results['O16'][i] = None
                results['O18'][i] = None
                results['c_16'][i] = None
                results['c_18'][i] = None
        handle.update_meta('results', results)
    handle.save_json()

