"""EasyEngine package installation using apt-get module."""
import apt
import sys


class EEAptGet():
    """Generic apt-get intialisation"""

    def update():
        """Similar to apt-get update"""
        # app.log.debug("Update cache")
        cache = apt.Cache()
        fprogress = apt.progress.text.AcquireProgress()
        iprogress = apt.progress.base.InstallProgress()
        cache.update(fprogress)
        cache.close()

    def upgrade(packages):
        """Similar to apt-get update"""
        cache = apt.Cache()
        fprogress = apt.progress.text.AcquireProgress()
        iprogress = apt.progress.base.InstallProgress()
        my_selected_packages = []
        # Cache Initialization
        if not cache:
            cache = apt.Cache()
        # Cache Read
        cache.open()
        for package in packages:
            pkg = cache[package]
            # Check Package Installed
            if pkg.is_installed:
                # Check Package is Upgradeble
                if pkg.is_upgradable:
                    with cache.actiongroup():
                        # Mark Package for Upgrade
                        pkg.mark_upgrade()
                    my_selected_packages.append(pkg.installed)
                else:
                    print("\'{package_name}-{package_ver.version}\'"
                          "already the newest version"
                          .format(package_name=pkg.name,
                                  package_ver=pkg.installed))

        # Check if packages available for install.
        if len(my_selected_packages) > 0:
            print("The following packages will be upgraded:"
                  "\n {pkg_name}"
                  .format(pkg_name=my_selected_packages))
            print("{pkg_install_count} newly installed."
                  .format(pkg_upgrade_count=len(my_selected_packages)))
            print("Need to get {req_download} bytes of archives"
                  .format(req_download=cache.required_download))
            print("After this operation, {space} bytes of"
                  "additional disk space will be used."
                  .format(space=cache.required_space))
            try:
                # Commit changes in cache (actually install)
                cache.commit(fprogress, iprogress)
            except Exception as e:
                print("package installation failed. [{err}]"
                      .format(err=str(e)))
                return(False)
        return(True)

    def install(packages):
        """Installation of packages"""
        cache = apt.Cache()
        fprogress = apt.progress.text.AcquireProgress()
        iprogress = apt.progress.base.InstallProgress()
        my_selected_packages = []
        # Cache Initialization
        if not cache:
            cache = apt.Cache()
        # Cache Read
        cache.open()

        for package in packages:
            try:
                pkg = cache[package]
            except KeyError as e:
                continue
            # Check Package Installed
            if pkg.is_installed or pkg.marked_install:
                # Check Package is Upgradeble
                if pkg.is_upgradable:
                    print("latest version of \'{package_name}\' available."
                          .format(package_name=pkg.installed))
                else:
                    # Check if package already marked for install
                    if not pkg.marked_install:
                        print("\'{package_name}-{package_ver}\'"
                              "already the newest version"
                              .format(package_name=pkg.shortname,
                                      package_ver=pkg.installed))
            else:
                with cache.actiongroup():
                    # Mark Package for Installation
                    pkg.mark_install()
                my_selected_packages.append(pkg.name)

        # Check if packages available for install.
        if cache.install_count > 0:
            print("The following NEW packages will be installed:"
                  "\n {pkg_name}"
                  .format(pkg_name=my_selected_packages))
            print("{pkg_install_count} newly installed."
                  .format(pkg_install_count=cache.install_count))
            print("Need to get {req_download} bytes of archives"
                  .format(req_download=cache.required_download))
            print("After this operation, {space} bytes of"
                  "additional disk space will be used."
                  .format(space=cache.required_space))
            try:
                # Commit changes in cache (actually install)
                cache.commit(fprogress, iprogress)
            except Exception as e:
                print("package installation failed. [{err}]"
                      .format(err=str(e)))
                return(False)
                cache.close()
        cache.close()
        return(True)

    def remove(packages, auto=True, purge=False):
        def __dependencies_loop(cache, deplist, pkg, onelevel=True):
            """ Loops through pkg's dependencies.
            Returns a list with every package found. """
            print("Inside")
            if onelevel:
                onelevellist = []
            if not pkg.is_installed:
                return
            for depf in pkg.installed.dependencies:
                for dep in depf:
                    if (dep.name in cache and not cache[dep.name]
                       in deplist):
                        deplist.append(cache[dep.name])
                        __dependencies_loop(cache, deplist, cache[dep.name])
                    if onelevel:
                        if dep.name in cache:
                            onelevellist.append(cache[dep.name])
            if onelevel:
                return onelevellist

        cache = apt.Cache()
        fprogress = apt.progress.text.AcquireProgress()
        iprogress = apt.progress.base.InstallProgress()

        my_selected_packages = []
        # Cache Initialization
        if not cache:
            cache = apt.Cache()
        # Cache Read
        cache.open()
        for package in packages:
            print("processing", package)
            package = cache[package]
            if not package.is_installed:
                print("Package '{package_name}' is not installed,"
                      " so not removed."
                      .format(package_name=package.name))
                continue
            if package.marked_delete:
                continue
            else:
                my_selected_packages.append(package.name)
            # How logic works:
            # 1) We loop trough dependencies's dependencies and add them to
            # the list.
            # 2) We sequentially remove every package in list
            # - via is_auto_installed we check if we can safely remove it
            deplist = []
            onelevel = __dependencies_loop(cache, deplist, package,
                                           onelevel=True)
            # Mark for deletion the first package, to fire up auto_removable
            # Purge?
            if purge:
                package.mark_delete(purge=True)
            else:
                package.mark_delete(purge=False)
            # Also ensure we remove AT LEAST the first level of dependencies
            # (that is, the actual package's dependencies).
            if auto:
                markedauto = []
                for pkg in onelevel:
                    if (not pkg.marked_install and pkg.is_installed
                       and not pkg.is_auto_installed):
                        pkg.mark_auto()
                        markedauto.append(pkg)

                for pkg in deplist:
                    if (not pkg.marked_install and pkg.is_installed and
                       pkg.is_auto_removable):
                        # Purge?
                        if purge:
                            pkg.mark_delete(purge=True)
                        else:
                            pkg.mark_delete(purge=False)
                # Restore auted items
                for pkg in markedauto:
                    if not pkg.marked_delete:
                        pkg.mark_auto(False)
            else:
                # We need to ensure that the onelevel packages are not marked
                # as automatically installed, otherwise the user may drop
                # them via autoremove or aptitude.
                for pkg in onelevel:
                    if pkg.is_installed and pkg.is_auto_installed:
                        pkg.mark_auto(auto=False)

        # Check if packages available for remove/update.
        if cache.delete_count > 0:
            # app.log.debug('packages will be REMOVED ')
            print("The following packages will be REMOVED:"
                  "\n {pkg_name}"
                  .format(pkg_name=my_selected_packages))
            print("{pkg_remove_count} to remove."
                  .format(pkg_remove_count=cache.delete_count))
            # app.log.debug('bytes disk space will be freed')
            print("After this operation, {space} bytes disk spac"
                  "e will be freed.".format(space=cache.required_space))
            try:
                cache.commit(fprogress, iprogress)
            except Exception as e:
                # app.log.error('Sorry, package installation failed ')
                print("Sorry, package installation failed [{err}]"
                      .format(err=str(e)))
                cache.close()
                return(False)
        cache.close()
        return(True)

    def is_installed(package):
        cache = apt.Cache()
        fprogress = apt.progress.text.AcquireProgress()
        iprogress = apt.progress.base.InstallProgress()

        # Cache Initialization
        if not cache:
            cache = apt.Cache()
        # Cache Read
        cache.open()
        pkg = cache[package]
        # Check Package Installed
        if pkg.is_installed:
            cache.close()
            return True
        else:
            cache.close()
            return False
