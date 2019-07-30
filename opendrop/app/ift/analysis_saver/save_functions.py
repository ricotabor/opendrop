import configparser
import csv
import math
from collections import OrderedDict
from pathlib import Path
from typing import Sequence, Tuple, Iterable

import cv2
import numpy as np

from opendrop.app.common.analysis_saver.misc import simple_grapher
from opendrop.app.ift.analysis import IFTDropAnalysis
from opendrop.utility.misc import clear_directory_contents
from .model import IFTAnalysisSaverOptions


def save_drops(drops: Iterable[IFTDropAnalysis], options: IFTAnalysisSaverOptions) -> None:
    drops = list(drops)

    full_dir = options.save_root_dir
    assert full_dir.is_dir() or not full_dir.exists()
    full_dir.mkdir(parents=True, exist_ok=True)
    clear_directory_contents(full_dir)

    padding = len(str(len(drops)))
    dir_name = options.bn_save_dir_name.get()
    for i, drop in enumerate(drops):
        drop_dir_name = dir_name + '{n:0>{padding}}'.format(n=(i+1), padding=padding)  # i+1 for 1-based indexing.
        _save_individual(drop, drop_dir_name, options)

    if len(drops) <= 1:
        return

    figure_opts = options.ift_figure_opts
    if figure_opts.bn_should_save.get():
        fig_size = figure_opts.size
        dpi = figure_opts.bn_dpi.get()
        with (full_dir/'ift_plot.png').open('wb') as out_file:
            _save_ift_figure(
                drops=drops,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)

    figure_opts = options.volume_figure_opts
    if figure_opts.bn_should_save.get():
        fig_size = figure_opts.size
        dpi = figure_opts.bn_dpi.get()
        with (full_dir/'volume_plot.png').open('wb') as out_file:
            _save_volume_figure(
                drops=drops,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)

    figure_opts = options.surface_area_figure_opts
    if figure_opts.bn_should_save.get():
        fig_size = figure_opts.size
        dpi = figure_opts.bn_dpi.get()
        with (full_dir/'surface_area_plot.png').open('wb') as out_file:
            _save_surface_area_figure(
                drops=drops,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)

    with (full_dir/'timeline.csv').open('w', newline='') as out_file:
        _save_timeline_data(drops, out_file)


def _save_individual(drop: IFTDropAnalysis, drop_dir_name: str, options: IFTAnalysisSaverOptions) -> None:
    full_dir = options.save_root_dir/drop_dir_name
    full_dir.mkdir(parents=True)

    _save_drop_image(drop, out_file_path=full_dir / 'image_original.png')
    _save_drop_image_annotated(drop, out_file_path=full_dir / 'image_annotated.png')

    with (full_dir/'params.ini').open('w') as out_file:
        _save_drop_params(drop, out_file=out_file)

    with (full_dir/'profile_extracted.csv').open('wb') as out_file:
        _save_drop_contour(drop, out_file=out_file)

    with (full_dir/'profile_fit.csv').open('wb') as out_file:
        _save_drop_contour_fit(drop, out_file=out_file)

    with (full_dir/'profile_fit_residuals.csv').open('wb') as out_file:
        _save_drop_contour_fit_residuals(drop, out_file=out_file)

    drop_residuals_figure_opts = options.drop_residuals_figure_opts
    if drop_residuals_figure_opts.bn_should_save.get():
        fig_size = drop_residuals_figure_opts.size
        dpi = drop_residuals_figure_opts.bn_dpi.get()
        with (full_dir/'profile_fit_residuals_plot.png').open('wb') as out_file:
            _save_drop_contour_fit_residuals_figure(
                drop=drop,
                out_file=out_file,
                fig_size=fig_size,
                dpi=dpi)


def _save_drop_image(drop: IFTDropAnalysis, out_file_path: Path) -> None:
    if drop.is_image_replicated:
        # A copy of the image already exists somewhere, we don't need to save it again.
        return

    image = drop.bn_image.get()
    if image is None:
        return

    cv2.imwrite(str(out_file_path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def _save_drop_image_annotated(drop: IFTDropAnalysis, out_file_path: Path) -> None:
    image = drop.bn_image.get()
    if image is None:
        return

    # Draw on a copy
    image = image.copy()

    needle_profile_extract = drop.bn_needle_profile_extract.get()
    if needle_profile_extract is not None:
        # Draw extracted needle edges
        image = cv2.polylines(
            img=image,
            pts=needle_profile_extract,
            isClosed=False,
            color=(0, 128, 255),
            thickness=1,
            lineType=cv2.LINE_AA)

    drop_profile_extract = drop.bn_drop_profile_extract.get()
    if drop_profile_extract is not None:
        # Draw extracted drop profile
        image = cv2.polylines(
            img=image,
            pts=[drop_profile_extract],
            isClosed=False,
            color=(0, 128, 255),
            thickness=1,
            lineType=cv2.LINE_AA)

    # Draw fitted drop profile
    drop_contour_fit = drop.bn_drop_profile_fit.get()
    if drop_contour_fit is not None:
        drop_contour_fit = drop_contour_fit.astype(int)
        image = cv2.polylines(
            img=image,
            pts=[drop_contour_fit],
            isClosed=False,
            color=(255, 0, 128),
            thickness=1,
            lineType=cv2.LINE_AA)

    needle_region = drop.bn_needle_region.get()
    if needle_region is not None:
        # Draw needle region
        image = cv2.rectangle(
            img=image,
            pt1=tuple(needle_region.p0),
            pt2=tuple(needle_region.p1),
            color=(13, 26, 255),
            thickness=1)

    drop_region = drop.bn_drop_region.get()
    if drop_region is not None:
        # Draw drop region
        image = cv2.rectangle(
            img=image,
            pt1=tuple(drop_region.p0),
            pt2=tuple(drop_region.p1),
            color=(255, 26, 13),
            thickness=1,
        )

    cv2.imwrite(str(out_file_path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))


def _save_drop_params(drop: IFTDropAnalysis, out_file) -> None:
    root = configparser.ConfigParser(allow_no_value=True)
    root.read_dict(OrderedDict((
        ('Physical', OrderedDict((
            ('; all quantities are in SI units', None),
            ('timestamp', drop.bn_image_timestamp.get()),
            ('interfacial_tension', drop.bn_interfacial_tension.get()),
            ('volume', drop.bn_volume.get()),
            ('surface_area', drop.bn_surface_area.get()),
            ('apex_radius', drop.bn_apex_radius.get()),
            ('worthington', drop.bn_worthington.get()),
            ('bond_number', drop.bn_bond_number.get()),
        ))),
        ('Image', OrderedDict((
            ('; regions are defined by (left, top, right, bottom) tuples', None),
            ('drop_region', tuple(drop.bn_drop_region.get())),
            ('needle_region', tuple(drop.bn_needle_region.get())),
            ('apex_coordinates', tuple(drop.bn_apex_coords_px.get())),
            ('; needle width in pixels', None),
            ('needle_width', drop.bn_needle_width_px.get()),
            ('; angle is in degrees (positive is counter-clockwise)', None),
            ('image_angle', math.degrees(drop.bn_rotation.get())),
        ))),
    )))

    root.write(out_file)


def _save_drop_contour(drop: IFTDropAnalysis, out_file) -> None:
    drop_profile_extract = drop.bn_drop_profile_extract.get()
    if drop_profile_extract is None:
        return

    np.savetxt(out_file, drop_profile_extract, fmt='%.1f,%.1f')


def _save_drop_contour_fit(drop: IFTDropAnalysis, out_file) -> None:
    drop_contour_fit = drop.bn_drop_profile_fit.get()
    if drop_contour_fit is None:
        return

    np.savetxt(out_file, drop_contour_fit, fmt='%.1f,%.1f')


def _save_drop_contour_fit_residuals(drop: IFTDropAnalysis, out_file) -> None:
    residuals = drop.bn_residuals.get()
    if residuals is None:
        return

    np.savetxt(out_file, residuals, fmt='%g,%g')


def _save_drop_contour_fit_residuals_figure(drop: IFTDropAnalysis, out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    residuals = drop.bn_residuals.get()
    if residuals is None:
        return

    fig = simple_grapher(
        label_x=r'Arclength parameter',
        label_y='Residual',
        data_x=residuals[:, 0],
        data_y=residuals[:, 1],
        color='blue',
        marker='.',
        line_style='',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_ift_figure(drops: Sequence[IFTDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [
        drop
        for drop in drops
        if math.isfinite(drop.bn_image_timestamp.get()) and
           math.isfinite(drop.bn_interfacial_tension.get())
    ]

    start_time = min(drop.bn_image_timestamp.get() for drop in drops)
    data = (
        (
            drop.bn_image_timestamp.get() - start_time,
            drop.bn_interfacial_tension.get() * 1e3
        )
        for drop in drops
    )

    fig = simple_grapher(
        'Time (s)',
        'Interfacial tension (mN m⁻¹)',
        *zip(*data),
        marker='.',
        line_style='-',
        color='red',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_volume_figure(drops: Sequence[IFTDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [
        drop
        for drop in drops
        if math.isfinite(drop.bn_image_timestamp.get()) and
           math.isfinite(drop.bn_volume.get())
    ]

    start_time = min(drop.bn_image_timestamp.get() for drop in drops)
    data = (
        (
            drop.bn_image_timestamp.get() - start_time,
            drop.bn_volume.get() * 1e9
        )
        for drop in drops
    )

    fig = simple_grapher(
        'Time (s)',
        'Volume (mm³)',
        *zip(*data),
        marker='.',
        line_style='-',
        color='blue',
        fig_size=fig_size,
        dpi=dpi)

    fig.savefig(out_file)


def _save_surface_area_figure(drops: Sequence[IFTDropAnalysis], out_file, fig_size: Tuple[float, float], dpi: int) -> None:
    drops = [
        drop
        for drop in drops
        if math.isfinite(drop.bn_image_timestamp.get()) and
           math.isfinite(drop.bn_surface_area.get())
    ]

    start_time = min(drop.bn_image_timestamp.get() for drop in drops)
    data = (
        (
            drop.bn_image_timestamp.get() - start_time,
            drop.bn_surface_area.get() * 1e6
        )
        for drop in drops
    )

    fig = simple_grapher(
        'Time (s)',
        'Surface area (mm²)',
        *zip(*data),
        marker='.',
        line_style='-',
        color='green',
        fig_size=fig_size,
        dpi=dpi
    )

    fig.savefig(out_file)


def _save_timeline_data(drops: Sequence[IFTDropAnalysis], out_file) -> None:
    writer = csv.writer(out_file)
    writer.writerow([
        'Time (s)',
        'IFT (N/m)',
        'Volume (m3)',
        'Surface area (m2)',
        'Apex radius (m)',
        'Worthington',
        'Bond number',
        'Image angle (degrees)',
        'Apex x-coordinate (px)',
        'Apex y-coordinate (px)',
        'Needle width (px)',
    ])

    for drop in drops:
        writer.writerow([
            drop.bn_image_timestamp.get(),
            drop.bn_interfacial_tension.get(),
            drop.bn_volume.get(),
            drop.bn_surface_area.get(),
            drop.bn_apex_radius.get(),
            drop.bn_worthington.get(),
            drop.bn_bond_number.get(),
            math.degrees(drop.bn_rotation.get()),
            *drop.bn_apex_coords_px.get(),
            drop.bn_needle_width_px.get(),
        ])