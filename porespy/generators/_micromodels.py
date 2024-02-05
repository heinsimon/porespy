import numpy as np
import matplotlib.pyplot as plt
from nanomesh import Mesher2D
from porespy.generators import lattice_spheres, borders, spheres_from_coords
from porespy.tools import _insert_disks_at_points_parallel, extend_slice
import scipy.ndimage as spim
import scipy.stats as spst
from typing import List


__all__ = [
    'rectangular_pillars_array',
    'cylindrical_pillars_array',
    'cylindrical_pillars_mesh',
]


def _extract(im, shape, spacing, truncate, lattice):
    r"""
    A helper function to extract the correct sub-section of the pillar images
    generated by the functions in this file.
    """
    if lattice.startswith('s'):
        if truncate:
            end = shape
        else:
            end = (np.ceil(shape/spacing)*spacing).astype(int) + 1
        im = im[:end[0], :end[1]]
    if lattice.startswith('t'):
        new_shape = np.array(im.shape)
        im = spim.rotate(im, -45, order=0, reshape=False)
        a, b = (new_shape/2).astype(int)
        s = (slice(a, a+1, None), slice(b, b+1, None))
        if truncate:
            a, b = np.around(shape/2).astype(int)
            sx = extend_slice(slices=s, shape=im.shape, pad=[a, b])
            im = im[sx]
            im = im[:shape[0], :shape[1]]
        else:
            diag = np.around((spacing**2 + spacing**2)**0.5).astype(int)
            a, b = (np.ceil(shape/diag)*diag/2).astype(int)
            sx = extend_slice(slices=s, shape=im.shape, pad=[a, b])
            im = im[sx]
    return im


def rectangular_pillars_array(
    shape: List,
    spacing: int = 40,
    dist: str = 'uniform',
    dist_kwargs: dict = {'loc': 5, 'scale': 10},
    lattice: str = 'sc',
    truncate: bool = True,
    seed: int = None,
):
    r"""
    A 2D micromodel with rectangular pillars positioned on a lattice

    The model is generated by inserting rectangular sections of different widths
    between each pair of points. The size of pillars is controlled indirectly by
    the size of the openings.

    Parameters
    ----------
    shape : array_like
        The X, Y size of the desired image in pixels
    spacing : int
        The spacing in pixels betwen pore centers (junctions between pillars).
        If `lattice='tri'` this refers to the diagonal distance between pores.
    dist : str or scipy.stats object
        The statistical distribution to use for throat radii. If a `scipy.stats`
        object is given the `rvs` method is used directly. If a `str` is given
        then the corresponding `scipy.stats` object is creating using the arguments
        given by `dist_kwargds`.
    dist_kwargs : dict
        A dictionary of keyword arguments to use when instantiating the `scipy.stats`
        object specified by `dist` (if `str`) was given.
    lattice : str
        The type of lattice to use. Options are:

        ======== ===================================================================
        lattice  description
        ======== ===================================================================
        'sc'     A simple cubic lattice where the pillars are aligned vertically and
                 horizontally with the standard grid. In this case the meaning of
                 ``spacing``, ``Rmin`` and ``Rmax`` directly refers to the number of
                 pixels.
        'tri'    A triangular matrix, which is esentially a cubic matrix rotated 45
                 degrees. In this case the mean of ``spacing``, ``Rmin`` and ``Rmax``
                 refer to the length of a pixel.
        ======== ===================================================================

    truncate : bool
        A flag to indicate if the output should be truncated to the given `shape`
        or if the returned image should be expanded to span an even number of unit
        cells.  The default is `False`.
    seed : int
        The value to initialize numpy's random number generator. The default is
        `None` which results in a new realization each time this function is called.

    Returns
    -------
    im : ndarray
        An `ndarray` with `True` values indicating the void space.

    Examples
    --------
        `Click here
        <https://porespy.org/examples/generators/reference/rectangular_pillars_array.html>`_
        to view online example.
    """
    if len(shape) != 2:
        raise Exception('shape must be 2D for this function')
    if seed is not None:
        np.random.seed(seed)
    if isinstance(dist, str):
        f = getattr(spst, dist)(**dist_kwargs)
    shape = np.array(shape)
    new_shape = (np.ones_like(shape)*shape.max()*2).astype(int)
    if lattice.startswith('s'):
        pts = ~lattice_spheres(new_shape, r=1, spacing=spacing, offset=0)
    elif lattice.startswith('t'):
        pts = ~lattice_spheres(shape=new_shape, r=1, spacing=spacing, offset=0)
    labels = spim.label(pts)[0]
    tmp = np.zeros_like(pts)
    slices = spim.find_objects(labels)
    for s in slices:
        sx = extend_slice(
            slices=s,
            shape=pts.shape,
            pad=[np.around(f.rvs()).astype(int), spacing],
        )
        tmp[sx] = True
        sx = extend_slice(
            slices=s,
            shape=pts.shape,
            pad=[spacing, np.around(f.rvs()).astype(int)],
        )
        tmp[sx] = True
    tmp = _extract(tmp, shape, spacing, truncate, lattice)
    return tmp


def cylindrical_pillars_array(
    shape: List,
    spacing: int = 40,
    dist: str = 'uniform',
    dist_kwargs: dict = {'loc': 5, 'scale': 10},
    lattice: str = 'sc',
    truncate: bool = True,
    seed: int = None,
):
    r"""
    A 2D micromodel with cylindrical pillars positioned on a lattice

    The model is generated by inserting disks of different size at each point in
    the lattice. The size of the openings between pillars is controlled indirectly
    by the size of the pillars.

    Parameters
    ----------
    shape : array_like
        The X, Y size of the desired image in pixels
    spacing : int
        The spacing in pixels betwen pillar centers. If `lattice='tri'` this refers
        to the diagonal distance between pillars.
    dist : str or scipy.stats object
        The statistical distribution to use for pillar radii. If a `scipy.stats`
        object is given the `rvs` method is used directly. If a `str` is given
        then the corresponding `scipy.stats` object is creating using the arguments
        given by `dist_kwargds`.
    dist_kwargs : dict
        A dictionary of keyword arguments to use when instantiating the `scipy.stats`
        object specified by `dist` (if `str`) was given.
    lattice : str
        The type of lattice to use. Options are:

        ======== ===================================================================
        lattice  description
        ======== ===================================================================
        'sc'     A simple cubic lattice where the pillars are aligned vertically and
                 horizontally with the standard grid. In this case the meaning of
                 ``spacing``, ``Rmin`` and ``Rmax`` directly refers to the number of
                 pixels.
        'tri'    A triangular matrix, which is esentially a cubic matrix rotated 45
                 degrees. In this case the mean of ``spacing``, ``Rmin`` and ``Rmax``
                 refer to the length of a pixel.
        ======== ===================================================================

    truncate : bool
        A flag to indicate if the output should be truncated to the given `shape`
        or if the returned image should be expanded to span an even number of unit
        cells.  The default is `False`.
    seed : int
        The value to initialize numpy's random number generator. The default is
        `None` which results in a new realization each time this function is called.

    Returns
    -------
    im : ndarray
        An `ndarray` with `True` values indicating the void space.

    Examples
    --------
        `Click here
        <https://porespy.org/examples/generators/reference/cylindrical_pillars_array.html>`_
        to view online example.
    """
    if len(shape) != 2:
        raise Exception('shape must be 2D for this function')
    if seed is not None:
        np.random.seed(seed)
    if isinstance(dist, str):
        f = getattr(spst, dist)(**dist_kwargs)
    shape = np.array(shape)
    new_shape = (np.ones_like(shape)*shape.max()*2).astype(int)
    if lattice.startswith('s'):
        pts = ~lattice_spheres(new_shape, r=1, spacing=spacing, offset=0)
    elif lattice.startswith('t'):
        pts = ~lattice_spheres(new_shape, r=1, spacing=spacing, offset=0)
    coords = np.vstack(np.where(pts))
    radii = f.rvs(pts.sum())
    tmp = np.ones_like(pts, dtype=int)
    tmp = _insert_disks_at_points_parallel(
        im=tmp, coords=coords, radii=radii, v=0, smooth=True, overwrite=True)
    if lattice.startswith('s'):
        if truncate:
            end = shape
        else:
            end = (np.ceil(shape/spacing)*spacing).astype(int) + 1
        tmp = tmp[:end[0], :end[1]]
        pts = pts[:end[0], :end[1]]
    tmp = _extract(tmp, shape, spacing, truncate, lattice)
    pts = _extract(pts, shape, spacing, truncate, lattice)
    return tmp


def cylindrical_pillars_mesh(
    shape: list,
    f: float = 0.75,
    a: int = 1000,
    n: int = None,
    truncate : bool = True,
):
    r"""
    A 2D micromodel with randomly located cylindrical pillars of random radius

    The model is generated by inserting disks at each corner of a triangular mesh
    (generated using `nanomesh`). The size of the disks is a fraction of the
    maximally inscribed disk at each location.

    Parameter
    ---------
    shape : array_like
        The X, Y size of the desired image in pixels
    f : scalar
        A factor to control the relative size of the pillars. `f = 1` results in
        pillars that just touch each other, while `f < 1` will add more space
        between the pillars
    a : scalar
        Controls the number of pillars in the image, with a small value giving
        more pillars. The default is 1500.  Technically this parameter sets the
        minimum area for each triangle in the mesh.
    n : scalar
        Controls the distance between pillars on the edges. By default it uses
        $\sqrt{a}/f$, but it can be overwritten using this argument if needed.
    truncate : bool
        A flag to indicate if the output should be truncated to the given `shape`
        or if the returned image should be expanded to include the full boundary
        pillars.  The default is `True`.

    Returns
    -------
    im : ndarray
        A ndarray with pillars locations determined by generating a triangular mesh
        of the specified domain size and putting pillars at each vertex. Note that
        this process is deterministic for a given set of input arguments so the
        apparent randomness of the pillar locations is actually determined by the
        underlaying mesh package used (`nanomesh`).

    Examples
    --------
        `Click here
        <https://porespy.org/examples/generators/reference/cylindrical_pillars_mesh.html>`_
        to view online example.

    """
    if len(shape) != 2:
        raise Exception('shape must be 2D for this function')
    if n is None:
        n = a**0.5/f
    im = np.ones(shape, dtype=float)
    bd = borders(im.shape, mode='faces')
    im[bd] = 0.0

    mesher = Mesher2D(im)
    mesher.generate_contour(max_edge_dist=n)

    mesh = mesher.triangulate(opts=f'q0a{a}ne')
    # mesh.plot_pyvista(jupyter_backend='static', show_edges=True)
    tri = mesh.triangle_dict

    # TODO: The corners contain 2 (say A and B) points very close to each other.
    # The following if statement will ignore the connection between A and B when
    # checking for the maximal size; however, sometimes the max size will be between
    # A and some internal point when in fact B had an internal point as a neighbor
    # that was much closer, so the sphere ends up being too big. The following code
    # needs to handle this better.
    r_max = np.inf*np.ones([tri['vertices'].shape[0], ])
    for e in tri['edges']:
        L = np.sqrt(np.sum(np.diff(tri['vertices'][e], axis=0)**2))
        if L/2 > 1:
            r_max[e[0]] = min(r_max[e[0]], L/2)
            r_max[e[1]] = min(r_max[e[1]], L/2)

    mask = np.ravel(tri['vertex_markers'] >= 0)
    r = f*(r_max[mask])

    coords = tri['vertices'][mask]
    coords = np.pad(
        array=coords,
        pad_width=((0, 0), (0, 1)),
        mode='constant',
        constant_values=0,
    )
    coords = np.vstack((coords.T, r)).T
    if truncate:
        im_w_spheres = spheres_from_coords(coords, smooth=True, mode='extended')
    else:
        im_w_spheres = spheres_from_coords(coords, smooth=True, mode='contained')
    return ~im_w_spheres


if __name__ == "__main__":

    rect_demo = False
    cyl_demo = False
    rand_cyl = True

    if rect_demo:
        fig, ax = plt.subplots(2, 2)
        np.random.seed(0)
        im1 = rectangular_pillars_array(
            shape=[400, 600], spacing=40, lattice='simple', truncate=True)
        im2 = rectangular_pillars_array(
            shape=[400, 600], spacing=40, lattice='tri', truncate=True)

        ax[0][0].imshow(im1, origin='lower', interpolation='none')
        ax[0][1].imshow(im2, origin='lower', interpolation='none')

        np.random.seed(0)
        im1 = rectangular_pillars_array(
            shape=[400, 600], spacing=40, lattice='simple', truncate=False)
        im2 = rectangular_pillars_array(
            shape=[400, 600], spacing=40, lattice='tri', truncate=False)

        ax[1][0].imshow(im1, origin='lower', interpolation='none')
        ax[1][1].imshow(im2, origin='lower', interpolation='none')

    if cyl_demo:
        fig, ax = plt.subplots(2, 2)
        np.random.seed(0)
        im1 = cylindrical_pillars_array(
            shape=[400, 600], spacing=40, lattice='simple', truncate=True)
        im2 = cylindrical_pillars_array(
            shape=[400, 600], spacing=40, lattice='tri', truncate=True)
        ax[0][0].imshow(im1, origin='lower', interpolation='none')
        ax[0][1].imshow(im2, origin='lower', interpolation='none')

        np.random.seed(0)
        im1 = cylindrical_pillars_array(
            shape=[400, 600], spacing=40, lattice='simple', truncate=False)
        im2 = cylindrical_pillars_array(
            shape=[400, 600], spacing=40, lattice='tri', truncate=False)
        ax[1][0].imshow(im1, origin='lower', interpolation='none')
        ax[1][1].imshow(im2, origin='lower', interpolation='none')

    if rand_cyl:
        im = cylindrical_pillars_mesh(
            shape=[1000, 500],
            n=40,
        )
        plt.imshow(im)
