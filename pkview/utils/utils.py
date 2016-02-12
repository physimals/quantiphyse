import yaml
import nibabel as nib


def yaml_loader(filepath):
    with open(filepath, "r") as fd:
        data = yaml.load(fd)
    return data


def save_file(file1, hdr, data1):
    # get header
    header1 = hdr

    # modify header
    shp1 = header1.get_data_shape()
    header1.set_data_shape(shp1[:-1])
    header1.set_data_dtype(data1.dtype)

    # Save the current overlay or save a specific overlay
    img1 = nib.Nifti1Image(data1, header1.get_base_affine(), header=header1)
    # Save image
    img1.to_filename(file1)