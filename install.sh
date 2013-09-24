pkg_install='python2.7 setup.py install'
cwd=`pwd`

InstallPython()
{
    echo "Installing python2.7"
    tar -zxvf lib/Python-2.7.tgz
    cd Python-2.7 && sh ./configure && make
    sudo make install && cd $cwd
    sudo rm -rf Python-2.7
}

InstallYaml()
{
    #install setuptools
    echo "Installing PyYAML"
    tar -zxvf lib/setuptools-0.6c11.tar.gz
    cd setuptools-0.6c11
    sudo $pkg_install && cd $cwd
    #install pyyaml
    tar -zxvf lib/PyYAML-3.10.tar.gz
    cd PyYAML-3.10
    sudo $pkg_install && cd $cwd
    sudo rm -rf PyYAML-3.10 && sudo rm -rf setuptools-0.6c11
}
pyv=`which python2.7 2>&1| awk -F: '{print $1}' | awk -F'/' '{print $NF}'`
if [ "$pyv" = "python2.7" ]
then
    echo "python2.7 have been installed"
    info=`python2.7 -m yaml 2>&1 | awk -F: '{print $2}'`
    if [ "$info" = " No module named yaml" ] 
    then
       echo "Installing yaml"
       InstallYaml
    fi
else
    InstallPython
    InstallYaml
fi
