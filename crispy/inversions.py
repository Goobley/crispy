from typing import Union, Dict, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
import zarr
from matplotlib.colors import SymLogNorm
from astropy.wcs import WCS
import astropy.units as u
from astropy.coordinates import SkyCoord
from sunpy.coordinates import Helioprojective
from .mixin import InversionSlicingMixin
from .utils import ObjDict

rc_context_dict = {
    # "figure.constrained_layout.use" : True,
    # "figure.autolayout" : True,
    "savefig.bbox": "tight",
    "font.family": "serif",
    "image.origin": "lower",
    "figure.figsize": (10, 6),
    # "image.aspect" : "auto"
    "font.size": 11,
    "font.serif": "New Century Schoolbook",
}


class Inversion(InversionSlicingMixin):
    """
    Class for transporting and using the inversions obtained from RADYNVERSION.

    Parameters
    ----------
    filename : str or ObjDict
        The file of the inversion. Can be either a zarr file path or a
        ``crispy.utils.ObjDict`` object.
    header : dict
        The header information of the associated observation.
    z : str or numpy.ndarray or None, optional
        The height grid that the atmospheric parameters are calculated at. This
        can be either a zarr file path or a numpy.ndarray. Defaults to None
        which assumes that ``filename`` contains a path "/atmos/z" when
        ``filename`` is a string or an entry with key ``z`` when ``filename is a
        ``crispy.utils.ObjDict`` object.
    wcs : astropy.wcs.WCS or None, optional
        The WCS of the observation associated with the inversions. Default is
        None, the WCS is inferred from the inversion and header.
    """

    def __init__(
        self,
        filename: Union[str, ObjDict],
        header: Dict,
        z: Optional[Union[str, np.ndarray]] = None,
        wcs: Optional[WCS] = None,
    ) -> None:
        if isinstance(filename, str):
            self.f = zarr.open(filename, mode="r")
            if isinstance(z, str):
                self.z = zarr.open(z, mode="r")["z"][:]
            elif z is None:
                self.z = self.f["/atmos/z"]
            else:
                self.z = z
            if wcs is None:
                self.wcs = self._inversion_wcs(header)
            else:
                self.wcs = wcs
            self.header = header
        elif isinstance(filename, ObjDict):
            self.f = filename
            if isinstance(z, str):
                self.z = zarr.open(z, mode="r")["z"][:]
            elif z is None:
                self.z = filename["z"]
            else:
                self.z = z
            if wcs is None:
                self.wcs = self._inversion_wcs(header)
            else:
                self.wcs = wcs
            self.header = header

    @property
    def ne(self):
        """
        Returns the electron number density in the inversion.
        """
        if isinstance(self.f, ObjDict):
            return self.f["ne"]
        else:
            return self.f["/atmos/ne"]

    @property
    def temp(self):
        """
        Returns the electron temperature in the inversion.
        """
        if isinstance(self.f, ObjDict):
            return self.f["temperature"]
        else:
            return self.f["/atmos/temperature"]

    @property
    def vel(self):
        """
        Returns the bulk velocity flow in the inversion.
        """
        if isinstance(self.f, ObjDict):
            return self.f["vel"]
        else:
            return self.f["/atmos/vel"]

    @property
    def ne_err(self):
        """
        Returns the errors on the electron number density.
        """
        if isinstance(self.f, ObjDict):
            return self.f["ne_err"]
        else:
            return self.f["/atmos/ne_err"]

    @property
    def temp_err(self):
        """
        Returns the errors on the electron temperature.
        """
        if isinstance(self.f, ObjDict):
            return self.f["temperature_err"]
        else:
            return self.f["/atmos/temperature_err"]

    @property
    def vel_err(self):
        """
        Returns the errors on the bulk velocity flow.
        """
        if isinstance(self.f, ObjDict):
            return self.f["vel_err"]
        else:
            return self.f["/atmos/vel_err"]

    def __str__(self) -> str:
        try:
            time = self.header["DATE-AVG"][-12:]
            date = self.header["DATE-AVG"][:-13]
            pointing_x = str(self.header["CRVAL1"])
            pointing_y = str(self.header["CRVAL2"])
        except KeyError:
            time = self.header["time_obs"]
            date = self.header["date_obs"]
            pointing_x = str(self.header["crval"][-1])
            pointing_y = str(self.header["crval"][-2])

        return f"""Inversion
        ------------------
        {date} {time}

        Pointing: ({pointing_x}, {pointing_y})"""

    def _inversion_wcs(self, header: Dict) -> WCS:

        wcs_dict = {}

        try:
            wcs_dict["NAXIS1"] = header["NAXIS1"]
            wcs_dict["NAXIS2"] = header["NAXIS2"]
            wcs_dict["NAXIS3"] = self.z.shape[0]

            wcs_dict["CTYPE1"] = "HPLN-TAN"
            wcs_dict["CTYPE2"] = "HPLT-TAN"
            wcs_dict["CTYPE3"] = "HEIGHT"

            wcs_dict["CUNIT1"] = "arcsec"
            wcs_dict["CUNIT2"] = "arcsec"
            wcs_dict["CUNIT3"] = "Mm"

            wcs_dict["CRPIX1"] = header["CRPIX1"]
            wcs_dict["CRPIX2"] = header["CRPIX2"]
            wcs_dict["CRPIX3"] = self.z.shape[0] // 2

            wcs_dict["CRVAL1"] = header["CRVAL1"]
            wcs_dict["CRVAL2"] = header["CRVAL2"]
            wcs_dict["CRVAL3"] = self.z[self.z.shape[0] // 2]

            wcs_dict["CDELT1"] = header["CDELT1"]
            wcs_dict["CDELT2"] = header["CDELT2"]
            wcs_dict["CDELT3"] = 1.0  # z is sampled non-uniformly
        except KeyError:
            wcs_dict["NAXIS1"] = header["dimensions"][-1]
            wcs_dict["NAXIS2"] = header["dimensions"][-2]
            wcs_dict["NAXIS3"] = self.z.shape[0]

            wcs_dict["CTYPE1"] = "HPLN-TAN"
            wcs_dict["CTYPE2"] = "HPLT-TAN"
            wcs_dict["CTYPE3"] = "HEIGHT"

            wcs_dict["CUNIT1"] = "arcsec"
            wcs_dict["CUNIT2"] = "arcsec"
            wcs_dict["CUNIT3"] = "Mm"

            wcs_dict["CRPIX1"] = header["crpix"][-1]
            wcs_dict["CRPIX2"] = header["crpix"][-2]
            wcs_dict["CRPIX3"] = self.z.shape[0] // 2

            wcs_dict["CRVAL1"] = header["crval"][-1]
            wcs_dict["CRVAL2"] = header["crval"][-2]
            wcs_dict["CRVAL3"] = self.z[self.z.shape[0] // 2]

            wcs_dict["CDELT1"] = header["pixel_scale"]
            wcs_dict["CDELT2"] = header["pixel_scale"]
            wcs_dict["CDELT3"] = 1.0  # z is sampled non-uniformly

        return WCS(wcs_dict)

    @plt.rc_context(rc_context_dict)
    def plot_ne(self, eb: bool = False) -> None:
        """
        Class method to plot the electron number density for a given location
        within the field-of-view. This works by slicing the ``Inversion``
        object.

        Parameters
        ----------
        eb : bool, optional
            Whether or not to plot the median absolute deviation (MAD) for the
            electron number density as errorbars. Default is False.
        """
        try:
            datetime = self.header["DATE-AVG"]
        except KeyError:
            datetime = self.header["date_obs"] + "T" + self.header["time_obs"]

        title = f"{datetime}"
        fig = plt.figure()
        ax1 = fig.gca()
        if eb:
            ax1.errorbar(self.z, self.ne, yerr=self.ne_err, capsize=3)
        else:
            ax1.plot(self.z, self.ne)
        ax1.set_ylabel(r"log$_{10}$ n$_{\text{e}}$ \[cm$^{-3}$\]")
        ax1.set_xlabel("z [Mm]")
        ax1.set_title(f"Electron Number Density {title}")
        fig.show()

    @plt.rc_context(rc_context_dict)
    def plot_temp(self, eb: bool = False) -> None:
        """
        Class method to plot the electron temperature for a given point in the
        field-of-view. This is done by slicing the ``Inversion`` object.

        Parameters
        ----------
        eb : bool, optional
            Whether or not to plot the median absolute deviation (MAD) of the
            estimated electron temperatures as errorbars. Default is False.
        """
        try:
            datetime = self.header["DATE-AVG"]
        except KeyError:
            datetime = self.header["date_obs"] + "T" + self.header["time_obs"]

        title = f"{datetime}"
        fig = plt.figure()
        ax1 = fig.gca()
        if eb:
            ax1.errorbar(self.z, self.temp, yerr=self.temp_err, capsize=3)
        else:
            ax1.plot(self.z, self.temp)
        ax1.set_ylabel(r"log$_{10}$ T \[K\]")
        ax1.set_xlabel("z [Mm]")
        ax1.set_title(f"Electron Temperature {title}")
        fig.show()

    @plt.rc_context(rc_context_dict)
    def plot_vel(self, eb: bool = False) -> None:
        """
        Class method to plot the bulk velocity for a certain point within the
        field-of-view. This is done using a slice of the ``Inversion`` instance.

        Parameters
        ----------
        eb : bool, optional
            Whether or not to plot the median absolute deviation (MAD) of the
            bulk velocity as errorbars. Default is False.
        """
        try:
            datetime = self.header["DATE-AVG"]
        except KeyError:
            datetime = self.header["date_obs"] + "T" + self.header["time_obs"]

        title = f"{datetime}"
        fig = plt.figure()
        ax1 = fig.gca()
        if eb:
            ax1.errorbar(self.z, self.vel, yerr=self.vel_err, capsize=3)
        else:
            ax1.plot(self.z, self.vel)
        ax1.set_ylabel(r"Bulk Plasma Flow \[km s$^{-1}$\]")
        ax1.set_xlabel("z [Mm]")
        ax1.set_title(f"Bulk Plasma Flow {title}")
        fig.show()

    @plt.rc_context(rc_context_dict)
    def plot_params(self, eb: bool = False) -> None:
        """
        Class method to plot the electron number density, electron temperature,
        and bulk velocity for a certain point within the field-of-view. This is
        done using a slice of the ``Inversion`` instance.

        Parameters
        ----------
        eb : bool, optional
            Whether or not to plot the median absolute deviation (MAD) for each
            estimated quantity as errorbars. Default is False.
        """
        try:
            datetime = self.header["DATE-AVG"]
        except KeyError:
            datetime = self.header["date_obs"] + "T" + self.header["time_obs"]

        title = f"{datetime}"
        fig = plt.figure()
        fig.suptitle(title)
        ax1 = fig.add_subplot(1, 3, 1)
        if eb:
            ax1.errorbar(self.z, self.ne, yerr=self.ne_err, capsize=3)
        else:
            ax1.plot(self.z, self.ne)
        ax1.set_ylabel(r"log$_{10}$ n$_{e}$ \[cm$^{-3}$\]")
        ax1.set_xlabel("z [Mm]")
        ax1.set_title("Electron Number Density")

        ax2 = fig.add_subplot(1, 3, 2)
        if eb:
            ax2.errorbar(self.z, self.temp, yerr=self.temp_err, capsize=3)
        else:
            ax2.plot(self.z, self.temp)
        ax2.set_ylabel(r"log$_{10}$ T \[K\]")
        ax2.set_xlabel("z [Mm]")
        ax2.set_title("Electron Temperature")

        ax3 = fig.add_subplot(1, 3, 3)
        if eb:
            ax3.errorbar(self.z, self.vel, yerr=self.vel_err, capsize=3)
        else:
            ax3.plot(self.z, self.vel)
        ax3.set_ylabel(r"Bulk Plasma Flow \[km s$^{-1}\]")
        ax3.set_xlabel("z [Mm]")
        ax3.set_title("Bulk Plasma Flow")
        fig.show()

    @plt.rc_context(rc_context_dict)
    def ne_map(self, frame: Optional[str] = None) -> None:
        """
        Creates an electron density map at a specified height denoted in the
        ``Inversion`` slice.

        Parameters
        ----------
        frame : str, optional
            The frame to plot the map in. Default is None therefore uses the WCS
            frame. Other option is "pix" to plot in the pixel frame.
        """
        height = np.round(self.z, decimals=4)
        try:
            datetime = self.header["DATE-AVG"]
        except KeyError:
            datetime = self.header["date_obs"] + "T" + self.header["time_obs"]

        if frame is None:
            fig = plt.figure()
            ax1 = fig.add_subplot(1, 1, 1, projection=self.wcs.low_level_wcs)
            im1 = ax1.imshow(self.ne, cmap="cividis")
            ax1.set_ylabel("Helioprojective Latitude [arcsec]")
            ax1.set_xlabel("Helioprojective Longitude [arcsec]")
            ax1.set_title(f"Electron Number Density {datetime} z={height}Mm")
            fig.colorbar(im1, ax=ax1, label=r"log$_{10}$n$_{e}$ [cm$^{-3}$]")
            fig.show()
        else:
            fig = plt.figure()
            ax1 = fig.gca()
            im1 = ax1.imshow(self.ne, cmap="cividis")
            ax1.set_ylabel("y [pixels]")
            ax1.set_xlabel("x [pixels]")
            ax1.set_title(f"Electron Number Density {datetime} z={height}Mm")
            fig.colorbar(im1, ax=ax1, label=r"log$_{10}$n$_{e}$ [cm$^{-3}$]")
            fig.show()

    @plt.rc_context(rc_context_dict)
    def temp_map(self, frame: Optional[str] = None) -> None:
        """
        Creates an electron temperature map at a specified height denoted in the
        ``Inversion`` slice.

        Parameters
        ----------
        frame : str, optional
            The frame to plot the map in. Default is None therefore uses the WCS
            frame. Other option is "pix" to plot in the pixel frame.
        """
        height = np.round(self.z, decimals=4)
        try:
            datetime = self.header["DATE-AVG"]
        except KeyError:
            datetime = self.header["date_obs"] + "T" + self.header["time_obs"]
        if frame is None:
            fig = plt.figure()
            ax1 = fig.add_subplot(1, 1, 1, projection=self.wcs.low_level_wcs)
            im1 = ax1.imshow(self.temp, cmap="hot")
            ax1.set_ylabel("Helioprojective Latitude [arcsec]")
            ax1.set_xlabel("Helioprojective Longitude [arcsec]")
            ax1.set_title(f"Electron Temperature {datetime} z={height}Mm")
            fig.colorbar(im1, ax=ax1, label=r"log$_{10}$T [K]")
            fig.show()
        else:
            fig = plt.figure()
            ax1 = fig.gca()
            im1 = ax1.imshow(self.temp, cmap="cividis")
            ax1.set_ylabel("y [pixels]")
            ax1.set_xlabel("x [pixels]")
            ax1.set_title(f"Electron Temperature {datetime} z={height}Mm")
            fig.colorbar(im1, ax=ax1, label=r"log$_{10}$T [K]")
            fig.show()

    @plt.rc_context(rc_context_dict)
    def vel_map(self, frame: Optional[str] = None) -> None:
        """
        Creates a bulk velocity map at a specified height denoted in the
        ``Inversion`` slice.

        Parameters
        ----------
        frame : str, optional
            The frame to plot the map in. Default is None therefore uses the WCS
            frame. Other option is "pix" to plot in the pixel frame.
        """
        height = np.round(self.z, decimals=4)
        try:
            datetime = self.header["DATE-AVG"]
        except KeyError:
            datetime = self.header["date_obs"] + "T" + self.header["time_obs"]
        if frame is None:
            fig = plt.figure()
            ax1 = fig.add_subplot(1, 1, 1, projection=self.wcs.low_level_wcs)
            im1 = ax1.imshow(self.vel, cmap="RdBu", norm=SymLogNorm(1))
            ax1.set_ylabel("Helioprojective Latitude [arcsec]")
            ax1.set_xlabel("Helioprojective Longitude [arcsec]")
            ax1.set_title(f"Bulk Velocity Flow {datetime} z={height}Mm")
            fig.colorbar(im1, ax=ax1, label=r"v [kms$^{-1}$]")
            fig.show()
        else:
            fig = plt.figure()
            ax1 = fig.gca()
            im1 = ax1.imshow(self.vel, cmap="RdBu", norm=SymLogNorm(1))
            ax1.set_ylabel("y [pixels]")
            ax1.set_xlabel("x [pixels]")
            ax1.set_title(f"Bulk Velocity Flow {datetime} z={height}Mm")
            fig.colorbar(im1, ax=ax1, label=r"v [kms$^{-1}$]")
            fig.show()

    @plt.rc_context(rc_context_dict)
    def params_map(self, frame: Optional[str] = None) -> None:
        """
        Creates maps of electron number density, electron temperature, and bulk
        velocity at a specified height denoted in the ``Inversion`` slice.

        Parameters
        ----------
        frame : str, optional
            The frame to plot the map in. Default is None therefore uses the WCS
            frame. Other option is "pix" to plot in the pixel frame.
        """
        height = np.round(self.z, decimals=4)
        try:
            datetime = self.header["DATE-AVG"]
        except KeyError:
            datetime = self.header["date_obs"] + "T" + self.header["time_obs"]
        if frame is None:
            fig = plt.figure()
            fig.suptitle(f"{datetime} z={np.round(height,3)}Mm")
            ax1 = fig.add_subplot(1, 3, 1, projection=self.wcs.low_level_wcs)
            im1 = ax1.imshow(self.ne, cmap="cividis")
            ax1.set_ylabel("Helioprojective Latitude [arcsec]")
            ax1.set_xlabel("Helioprojective Longitude [arcsec]")
            ax1.set_title("Electron Number Density")
            fig.colorbar(
                im1,
                ax=ax1,
                orientation="vertical",
                label=r"log$_{10}$n$_{e}$ [cm$^{-3}$]",
            )

            ax2 = fig.add_subplot(1, 3, 2, projection=self.wcs.low_level_wcs)
            im2 = ax2.imshow(self.temp, cmap="hot")
            ax2.set_ylabel(" ")
            ax2.tick_params(axis="y", labelleft=False)
            ax2.set_xlabel("Helioprojective Longitude [arcsec]")
            ax2.set_title("Electron Temperature")
            fig.colorbar(im2, ax=ax2, orientation="vertical", label=r"log$_{10}$T [K]")

            ax3 = fig.add_subplot(1, 3, 3, projection=self.wcs.low_level_wcs)
            im3 = ax3.imshow(self.vel, cmap="RdBu", norm=SymLogNorm(1))
            ax3.set_ylabel(" ")
            ax3.tick_params(axis="y", labelleft=False)
            ax3.set_xlabel("Helioprojective Longitude [arcsec]")
            ax3.set_title("Bulk Velocity Flow")
            fig.colorbar(im3, ax=ax3, orientation="vertical", label=r"v [kms$^{-1}$]")
            fig.show()
        else:
            fig = plt.figure()
            ax1 = fig.add_subplot(1, 3, 1)
            im1 = ax1.imshow(self.ne, cmap="cividis")
            ax1.set_ylabel("y [pixels]")
            ax1.set_xlabel("x [pixels]")
            ax1.set_title("Electron Number Density")
            fig.colorbar(
                im1,
                ax=ax1,
                orientation="vertical",
                label=r"log$_{10}$n$_{e}$ [cm$^{-3}$]",
            )

            ax2 = fig.add_subplot(1, 3, 2)
            im2 = ax2.imshow(self.temp, cmap="hot")
            ax2.set_yticks([])
            ax2.set_xlabel("x [pixels]")
            ax2.set_title("Electron Temperature")
            fig.colorbar(im2, ax=ax2, orientation="vertical", label=r"log$_{10}$T [K]")

            ax3 = fig.add_subplot(1, 3, 3)
            im3 = ax3.imshow(self.vel, cmap="RdBu", norm=SymLogNorm(1))
            ax3.set_yticks([])
            ax3.set_xlabel("x [pixels]")
            ax3.set_title("Bulk Velocity Flow")
            fig.colorbar(im3, ax=ax3, orientation="vertical", label=r"v [kms$^{-1}$]")
            fig.show()

    def to_lonlat(
        self, y: int, x: int, coord: bool = False, unit: bool = False
    ) -> Tuple[float, float]:
        """
        This function will take a y, x coordinate in pixel space and map it to
        Helioprojective Longitude, Helioprojective Latitude according to the
        transform in the WCS. This will return the Helioprojective coordinates
        in units of arcseconds. Note this function takes arguments in the order
        of numpy indexing (y,x) but returns a pair longitude/latitude which is
        Solar-X, Solar-Y.

        Parameters
        ----------
        y : int
            The y-index to be converted to Helioprojective Latitude.
        x : int
            The x-index to be converted to Helioprojective Longitude.
        """
        if coord:
            if len(self.wcs.low_level_wcs.array_shape) == 4:
                if hasattr(self, "ind"):
                    if isinstance(self.ind[-2], slice) and isinstance(
                        self.ind[-1], slice
                    ):
                        return self.wcs.low_level_wcs._wcs[
                            0, 0, self.ind[-2], self.ind[-1]
                        ].array_index_to_world(y, x)
                    elif isinstance(self.ind[-2], slice) and not isinstance(
                        self.ind[-1], slice
                    ):
                        return self.wcs.low_level_wcs._wcs[
                            0, 0, self.ind[-2]
                        ].array_index_to_world(y, x)
                    elif not isinstance(self.ind[-2], slice) and isinstance(
                        self.ind[-1], slice
                    ):
                        return self.wcs.low_level_wcs._wcs[
                            0, 0, :, self.ind[-1]
                        ].array_index_to_world(y, x)
                    else:
                        return self.wcs.low_level_wcs._wcs[0, 0].array_index_to_world(
                            y, x
                        )
                else:
                    return self.wcs[0, 0].array_index_to_world(y, x)
            elif len(self.wcs.low_level_wcs.array_shape) == 3:
                if hasattr(self, "ind") and self.wcs.low_level_wcs._wcs.naxis == 4:
                    if isinstance(self.ind[-2], slice) and isinstance(
                        self.ind[-1], slice
                    ):
                        return self.wcs.low_level_wcs._wcs[
                            0, 0, self.ind[-2], self.ind[-1]
                        ].array_index_to_world(y, x)
                    elif isinstance(self.ind[-2], slice) and not isinstance(
                        self.ind[-1], slice
                    ):
                        return self.wcs.low_level_wcs._wcs[
                            0, 0, self.ind[-2]
                        ].array_index_to_world(y, x)
                    elif not isinstance(self.ind[-2], slice) and isinstance(
                        self.ind[-1], slice
                    ):
                        return self.wcs.low_level_wcs._wcs[
                            0, 0, :, self.ind[-1]
                        ].array_index_to_world(y, x)
                    else:
                        return self.wcs.low_level_wcs._wcs[0, 0].array_index_to_world(
                            y, x
                        )
                else:
                    if hasattr(self, "ind"):
                        if isinstance(self.ind[-2], slice) and isinstance(
                            self.ind[-1], slice
                        ):
                            return self.wcs.low_level_wcs._wcs[
                                0, self.ind[-2], self.ind[-1]
                            ].array_index_to_world(y, x)
                        elif isinstance(self.ind[-2], slice) and not isinstance(
                            self.ind[-1], slice
                        ):
                            return self.wcs.low_level_wcs._wcs[
                                0, self.ind[-2]
                            ].array_index_to_world(y, x)
                        elif not isinstance(self.ind[-2], slice) and isinstance(
                            self.ind[-1], slice
                        ):
                            return self.wcs.low_level_wcs._wcs[
                                0, :, self.ind[-1]
                            ].array_index_to_world(y, x)
                        else:
                            return self.wcs.low_level_wcs._wcs[0].array_index_to_world(
                                y, x
                            )
                    else:
                        return self.wcs[0].array_index_to_world(y, x)
            elif len(self.wcs.low_level_wcs.array_shape) == 2:
                return self.wcs.array_index_to_world(y, x)
            else:
                raise NotImplementedError("Too many or too little dimensions.")
        else:
            if unit:
                if len(self.wcs.low_level_wcs.array_shape) == 4:
                    if hasattr(self, "ind"):
                        if isinstance(self.ind[-2], slice) and isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, self.ind[-2], self.ind[-1]
                            ].array_index_to_world(y, x)
                            return sc.Tx, sc.Ty
                        elif isinstance(self.ind[-2], slice) and not isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, self.ind[-2]
                            ].array_index_to_world(y, x)
                            return sc.Tx, sc.Ty
                        elif not isinstance(self.ind[-2], slice) and isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, :, self.ind[-1]
                            ].array_index_to_world(y, x)
                            return sc.Tx, sc.Ty
                        else:
                            sc = self.wcs.low_level_wcs._wcs[0, 0].array_index_to_world(
                                y, x
                            )
                            return sc.Tx, sc.Ty
                    else:
                        sc = self.wcs[0, 0].array_index_to_world(y, x)
                        return sc.Tx, sc.Ty
                elif len(self.wcs.low_level_wcs.array_shape) == 3:
                    if hasattr(self, "ind") and self.wcs.low_level_wcs._wcs.naxis == 4:
                        if isinstance(self.ind[-2], slice) and isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, self.ind[-2], self.ind[-1]
                            ].array_index_to_world(y, x)
                            return sc.Tx, sc.Ty
                        elif isinstance(self.ind[-2], slice) and not isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, self.ind[-2]
                            ].array_index_to_world(y, x)
                            return sc.Tx, sc.Ty
                        elif not isinstance(self.ind[-2], slice) and isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, :, self.ind[-1]
                            ].array_index_to_world(y, x)
                            return sc.Tx, sc.Ty
                        else:
                            sc = self.wcs.low_level_wcs._wcs[0, 0].array_index_to_world(
                                y, x
                            )
                            return sc.Tx, sc.Ty
                    else:
                        if hasattr(self, "ind"):
                            if isinstance(self.ind[-2], slice) and isinstance(
                                self.ind[-1], slice
                            ):
                                sc = self.wcs.low_level_wcs._wcs[
                                    0, self.ind[-2], self.ind[-1]
                                ].array_index_to_world(y, x)
                                return sc.Tx, sc.Ty
                            elif isinstance(self.ind[-2], slice) and not isinstance(
                                self.ind[-1], slice
                            ):
                                sc = self.wcs.low_level_wcs._wcs[
                                    0, self.ind[-2]
                                ].array_index_to_world(y, x)
                                return sc.Tx, sc.Ty
                            elif not isinstance(self.ind[-2], slice) and isinstance(
                                self.ind[-1], slice
                            ):
                                sc = self.wcs.low_level_wcs._wcs[
                                    0, :, self.ind[-1]
                                ].array_index_to_world(y, x)
                                return sc.Tx, sc.Ty
                            else:
                                sc = self.wcs.low_level_wcs._wcs[
                                    0
                                ].array_index_to_world(y, x)
                                return sc.Tx, sc.Ty
                        else:
                            sc = self.wcs[0].array_index_to_world(y, x)
                            return sc.Tx, sc.Ty
                elif len(self.wcs.low_level_wcs.array_shape) == 2:
                    sc = self.wcs.array_index_to_world(y, x)
                    return sc.Tx, sc.Ty
                else:
                    raise NotImplementedError("Too many or too little dimensions.")
            else:
                if len(self.wcs.low_level_wcs.array_shape) == 4:
                    if hasattr(self, "ind"):
                        if isinstance(self.ind[-2], slice) and isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, self.ind[-2], self.ind[-1]
                            ].array_index_to_world(y, x)
                            return sc.Tx.value, sc.Ty.value
                        elif isinstance(self.ind[-2], slice) and not isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, self.ind[-2]
                            ].array_index_to_world(y, x)
                            return sc.Tx.value, sc.Ty.value
                        elif not isinstance(self.ind[-2], slice) and isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, :, self.ind[-1]
                            ].array_index_to_world(y, x)
                            return sc.Tx.value, sc.Ty.value
                        else:
                            sc = self.wcs.low_level_wcs._wcs[0, 0].array_index_to_world(
                                y, x
                            )
                            return sc.Tx.value, sc.Ty.value
                    else:
                        sc = self.wcs[0, 0].array_index_to_world(y, x)
                        return sc.Tx.value, sc.Ty.value
                elif len(self.wcs.low_level_wcs.array_shape) == 3:
                    if hasattr(self, "ind") and self.wcs.low_level_wcs._wcs.naxis == 4:
                        if isinstance(self.ind[-2], slice) and isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, self.ind[-2], self.ind[-1]
                            ].array_index_to_world(y, x)
                            return sc.Tx.value, sc.Ty.value
                        elif isinstance(self.ind[-2], slice) and not isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, self.ind[-2]
                            ].array_index_to_world(y, x)
                            return sc.Tx.value, sc.Ty.value
                        elif not isinstance(self.ind[-2], slice) and isinstance(
                            self.ind[-1], slice
                        ):
                            sc = self.wcs.low_level_wcs._wcs[
                                0, 0, :, self.ind[-1]
                            ].array_index_to_world(y, x)
                            return sc.Tx.value, sc.Ty.value
                        else:
                            sc = self.wcs.low_level_wcs._wcs[0, 0].array_index_to_world(
                                y, x
                            )
                            return sc.Tx.value, sc.Ty.value
                    else:
                        if hasattr(self, "ind"):
                            if isinstance(self.ind[-2], slice) and isinstance(
                                self.ind[-1], slice
                            ):
                                sc = self.wcs.low_level_wcs._wcs[
                                    0, self.ind[-2], self.ind[-1]
                                ].array_index_to_world(y, x)
                                return sc.Tx.value, sc.Ty.value
                            elif isinstance(self.ind[-2], slice) and not isinstance(
                                self.ind[-1], slice
                            ):
                                sc = self.wcs.low_level_wcs._wcs[
                                    0, self.ind[-2]
                                ].array_index_to_world(y, x)
                                return sc.Tx.value, sc.Ty.value
                            elif not isinstance(self.ind[-2], slice) and isinstance(
                                self.ind[-1], slice
                            ):
                                sc = self.wcs.low_level_wcs._wcs[
                                    0, :, self.ind[-1]
                                ].array_index_to_world(y, x)
                                return sc.Tx.value, sc.Ty.value
                            else:
                                sc = self.wcs.low_level_wcs._wcs[
                                    0
                                ].array_index_to_world(y, x)
                                return sc.Tx.value, sc.Ty.value
                        else:
                            sc = self.wcs[0].array_index_to_world(y, x)
                            return sc.Tx.value, sc.Ty.value
                elif len(self.wcs.low_level_wcs.array_shape) == 2:
                    sc = self.wcs.array_index_to_world(y, x)
                    return sc.Tx.value, sc.Ty.value
                else:
                    raise NotImplementedError("Too many or too little dimensions.")

    def from_lonlat(self, lon: float, lat: float) -> Tuple[float]:
        """
        This function takes a Helioprojective Longitude, Helioprojective
        Latitude pair and converts them to the y, x indices to index the object
        correctly. The function takes its arguments in the order Helioprojective
        Longitude, Helioprojective Latitude but returns the indices in the (y,x)
        format so that the output of this function can be used to directly index
        the object.

        Parameters
        ----------
        lon : float
            The Helioprojective Longitude in arcseconds.
        lat : float
            The Helioprojective Latitude in arcseconds.
        """
        lon, lat = lon << u.arcsec, lat << u.arcsec
        sc = SkyCoord(lon, lat, frame=Helioprojective)
        if len(self.wcs.low_level_wcs.array_shape) == 4:
            if hasattr(self, "ind"):
                if isinstance(self.ind[-2], slice) and isinstance(self.ind[-1], slice):
                    return self.wcs.low_level_wcs._wcs[
                        0, 0, self.ind[-2], self.ind[-1]
                    ].world_to_array_index(sc)
                elif isinstance(self.ind[-2], slice) and not isinstance(
                    self.ind[-1], slice
                ):
                    return self.wcs.low_level_wcs._wcs[
                        0, 0, self.ind[-2]
                    ].world_to_array_index(sc)
                elif not isinstance(self.ind[-2], slice) and isinstance(
                    self.ind[-1], slice
                ):
                    return self.wcs.low_level_wcs._wcs[
                        0, 0, :, self.ind[-1]
                    ].world_to_array_index(sc)
                else:
                    return self.wcs.low_level_wcs._wcs[0, 0].world_to_array_index(sc)
            else:
                return self.wcs[0, 0].world_to_array_index(lon, lat)
        elif len(self.wcs.low_level_wcs.array_shape) == 3:
            if hasattr(self, "ind") and self.wcs.low_level_wcs._wcs.naxis == 4:
                if isinstance(self.ind[-2], slice) and isinstance(self.ind[-1], slice):
                    return self.wcs.low_level_wcs._wcs[
                        0, 0, self.ind[-2], self.ind[-1]
                    ].world_to_array_index(sc)
                elif isinstance(self.ind[-2], slice) and not isinstance(
                    self.ind[-1], slice
                ):
                    return self.wcs.low_level_wcs._wcs[
                        0, 0, self.ind[-2]
                    ].world_to_array_index(sc)
                elif not isinstance(self.ind[-2], slice) and isinstance(
                    self.ind[-1], slice
                ):
                    return self.wcs.low_level_wcs._wcs[
                        0, 0, :, self.ind[-1]
                    ].world_to_array_index(sc)
                else:
                    return self.wcs.low_level_wcs._wcs[0, 0].world_to_array_index(sc)
            else:
                if hasattr(self, "ind"):
                    if isinstance(self.ind[-2], slice) and isinstance(
                        self.ind[-1], slice
                    ):
                        return self.wcs.low_level_wcs._wcs[
                            0, self.ind[-2], self.ind[-1]
                        ].world_to_array_index(sc)
                    elif isinstance(self.ind[-2], slice) and not isinstance(
                        self.ind[-1], slice
                    ):
                        return self.wcs.low_level_wcs._wcs[
                            0, self.ind[-2]
                        ].world_to_array_index(sc)
                    elif not isinstance(self.ind[-2], slice) and isinstance(
                        self.ind[-1], slice
                    ):
                        return self.wcs.low_level_wcs._wcs[
                            0, :, self.ind[-1]
                        ].world_to_array_index(sc)
                    else:
                        return self.wcs.low_level_wcs._wcs[0].world_to_array_index(sc)
                else:
                    return self.wcs[0].world_to_array_index(sc)
        elif len(self.wcs.low_level_wcs.array_shape) == 2:
            return self.wcs.world_to_array_index(sc)
        else:
            raise NotImplementedError("Too many or too little dimensions.")
