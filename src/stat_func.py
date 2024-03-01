import matplotlib.pyplot as plt
import contextily as cx

def rgb2hex(rgb_string):
    return '#%02x%02x%02x' % tuple([int(n) for n in rgb_string.split(",")])

def _get_midpoint(t):
    return t[0] + (t[1]-t[0])/2

def plot_overview(
    my_markersize, 
    my_linewidth,
    configs,
    colors,
    edges,
    muni,
    nature,
    agriculture,
    culture,
    verify,
    summer,
    facilities,
    service,
    pois
    ):

    proj_crs = configs["proj_crs"]
    study_area_name = configs["study_area_name"]

    # initiate plot
    fig, ax = plt.subplots(3,3, figsize = (30,20), sharex=True, sharey=True)

    # full network
    i = (0,0)
    edges.plot(
        ax=ax[i], 
        linewidth = 3,
        zorder = 1,
        color = "black",
        lw = 2
        )
    muni[muni["kommunekode"].isin(configs["municipalities"])].to_crs(proj_crs).boundary.plot(
        ax = ax[i],
        alpha = 0.5, 
        linewidth = 2,
        color = "black",
        linestyle = "--",
        zorder = 2
        )
    cx.add_basemap(
        ax=ax[i], 
        crs = proj_crs, 
        source = cx.providers.CartoDB.Voyager, 
        zorder = 0)
    ax[i].set_axis_off()
    length = round(edges.length.sum()/1000)
    ax[i].set_title(f"Full network, {length} km")

    # get ax midpoint coordinate (for potential text plotting)
    xbar = _get_midpoint(ax[i].get_xlim())
    ybar = _get_midpoint(ax[i].get_ylim())

    # nature network
    i = (0,1)
    ax[i].set_axis_off()
    if not nature.empty:
        edges.plot(
            ax=ax[i], 
            zorder = 0,
            color = "grey",
            linewidth = 1,
            linestyle = "-"
            )
        nature.plot(
            ax=ax[i], 
            zorder = 1, 
            color = colors["nature"],
            linewidth = my_linewidth
            )
        length = round(nature.length.sum()/1000)
        ax[i].set_title(f"Nature network, {length} km")
    else:
        ax[i].text(xbar, ybar, f"No nature data for {study_area_name}")
    

    # agriculture network
    i = (0,2)
    ax[i].set_axis_off()
    if not agriculture.empty:
        edges.plot(
            ax=ax[i], 
            zorder = 0,
            color = "grey",
            linewidth = 1,
            linestyle = "-"
            )
        agriculture.plot(
            ax=ax[i], 
            zorder = 1, 
            color = colors["agriculture"],
            linewidth = my_linewidth
            )
        length = round(agriculture.length.sum()/1000)
        ax[i].set_title(f"Agricultural network, {length} km")
    else:
        ax[i].text(xbar, ybar, f"No agriculture data for {study_area_name}")

    # culture network
    i = (1,0)
    ax[i].set_axis_off()
    if not culture.empty:
        edges.plot(
            ax=ax[i], 
            zorder = 0,
            color = "grey",
            linewidth = 1,
            linestyle = "-"
            )
        culture.plot(
            ax=ax[i], 
            zorder = 1, 
            color = colors["culture"],
            linewidth = my_linewidth
            )
        length = round(culture.length.sum()/1000)
        ax[i].set_title(f"Culture network, {length} km")
    else:
        ax[i].text(xbar, ybar, f"No culture data for {study_area_name}")

    i = (1,1)
    ax[i].set_axis_off()
    if not summer.empty:
        edges.plot(
            ax=ax[i], 
            zorder = 0,
            color = "grey",
            linewidth = 1,
            linestyle = "-"
        )
        summer.plot(
            ax=ax[i], 
            zorder = 1, 
            color = colors["summer"],
            linewidth = my_linewidth
            )
        length = round(summer.length.sum()/1000)
        ax[i].set_title(f"Summerhouse network, {length} km")
    else:
        ax[i].text(xbar, ybar, f"No summer house data for {study_area_name}")


    # verify network
    i = (1,2)
    ax[i].set_axis_off()
    if not verify.empty:
        edges.plot(
            ax=ax[i], 
            zorder = 0,
            color = "grey",
            linewidth = 1,
            linestyle = "-"
            )
        verify.plot(
            ax=ax[i], 
            zorder = 1, 
            color = colors["verify"],
            linewidth = my_linewidth,
            )
        length = round(verify.length.sum()/1000)
        ax[i].set_title(f"Areas to verify network, {length} km")
    else:
        ax[i].text(xbar, ybar, f"No areas to verify data for {study_area_name}")

    # facilities
    i = (2,0)
    ax[i].set_axis_off()
    if not facilities.empty:
        edges.plot(
            ax=ax[i], 
            zorder = 0,
            color = "grey",
            linewidth = 1,
            linestyle = "-"
            )
        if not facilities[facilities["withinreach"]==1].empty:
            facilities[facilities["withinreach"]==1].plot(
                ax=ax[i], 
                zorder = 1, 
                color = colors["facilities"],
                markersize = my_markersize
                )
        if not facilities[facilities["withinreach"]==0].empty:
            facilities[facilities["withinreach"]==0].plot(
                ax=ax[i], 
                zorder = 2, 
                color = colors["facilities_outside"],
                markersize = my_markersize
                )
        reached = len(facilities[facilities["withinreach"]==1])
        total = reached + len(facilities[facilities["withinreach"]==0])
        ax[i].set_title(f"Facilities network, {reached} of {total} points reached")
    else:
        ax[i].text(xbar, ybar, f"No facilities data for {study_area_name}")

    # service
    i = (2,1)
    ax[i].set_axis_off()
    if not service.empty:
        edges.plot(
            ax=ax[i], 
            zorder = 0,
            color = "grey",
            linewidth = 1,
            linestyle = "-"
            )
        if not service[service["withinreach"]==1].empty:
            service[service["withinreach"]==1].plot(
                ax=ax[i], 
                zorder = 1, 
                color = colors["service"],
                markersize = my_markersize
                )
        if not service[service["withinreach"]==0].empty:            
            service[service["withinreach"]==0].plot(
                ax=ax[i], 
                zorder = 2, 
                color = colors["service_outside"],
                markersize = my_markersize
                )
        reached = len(service[service["withinreach"]==1])
        total = reached + len(service[service["withinreach"]==0])
        ax[i].set_title(f"Service network, {reached} of {total} points reached")
    else:
        ax[i].text(xbar, ybar, f"No service data for {study_area_name}")

    # pois
    i = (2,2)
    ax[i].set_axis_off()
    if not pois.empty:
        edges.plot(
            ax=ax[i], 
            zorder = 0,
            color = "grey",
            linewidth = 1,
            linestyle = "-"
            )
        if not pois[pois["withinreach"]==1].empty:
            pois[pois["withinreach"]==1].plot(
                ax=ax[i], 
                zorder = 1, 
                color = colors["pois"],
                markersize = my_markersize
                )
        if not pois[pois["withinreach"]==0].empty:
            pois[pois["withinreach"]==0].plot(
                ax=ax[i], 
                zorder = 2, 
                color = colors["pois_outside"],
                markersize = my_markersize
                )
        reached = len(pois[pois["withinreach"]==1])
        total = reached + len(pois[pois["withinreach"]==0])
        ax[i].set_title(f"POIs network, {reached} of {total} points reached")
    else:
        ax[i].text(xbar, ybar, f"No POIs data for {study_area_name}")

    ### adjust subplots
    plt.subplots_adjust(wspace=0, hspace=0.1)

    plt.close()

    return fig