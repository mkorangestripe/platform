#!/bin/bash
# This script is based on the instructions in the following article:
# https://docs.appdynamics.com/22.1/en/infrastructure-visibility/machine-agent/install-the-machine-agent/linux-install-using-zip-with-bundled-jre

DESCRIPTION="This script installs the AppD machine agent from a zip file."
UPDATE_USAGE="INSTALL USAGE: sudo ./appd-linux-install.sh ma-linux.zip"
INSTALL_USAGE="UPDATE USAGE: sudo ./appd-linux-install.sh ma-linux.zip CONTROLLER NODE_NAME CONTROLLER_KEY 'MACHINE_PATH_BASE'"

CWD=$(pwd)
SUDO_USER=$(whoami)

APPD_USER="appdynamics-machine-agent"
APPD_DIR="/opt/appdynamics"
MA_DIR="machine-agent"
MA_DIR_BACKUP="machine-agent.bak"
CONTROLLER_INFO_FILE='conf/controller-info.xml'

SYSTEMD_APPD_MA_SERVICE="appdynamics-machine-agent.service"
SYSTEMD_SERVICE_DIR="/etc/systemd/system"

SYSV_APPD_MA_SERVICE="appdynamics-machine-agent"
SYSV_SERVICE_DIR="/etc/init.d"
SYSV_APPD_SYSCONFIG='/etc/sysconfig/appdynamics-machine-agent'

zip_file=$1
controller=$2
nodeName=$3
controllerKey=$4
machinePathBase=$5

generateControllerInfo () {
    cat << EOF > $MA_DIR/$CONTROLLER_INFO_FILE
<?xml version="1.0" encoding="UTF-8"?>
<controller-info>
  <controller-host>${controller}.saas.appdynamics.com</controller-host>
  <controller-port>443</controller-port>
  <controller-ssl-enabled>true</controller-ssl-enabled>
  <enable-orchestration>false</enable-orchestration>
  <unique-host-id>${nodeName}</unique-host-id>
  <account-access-key>${controllerKey}</account-access-key>
  <account-name>${controller}</account-name>
  <sim-enabled>true</sim-enabled>
  <machine-path>${machinePathBase}|${nodeName}</machine-path>
  <dotnet-compatibility-mode>false</dotnet-compatibility-mode>
  <docker-enabled>false</docker-enabled>
</controller-info>
EOF
}

# This script must be run with sudo and take either 1 or 5 arguments:
if [[ $SUDO_USER != 'root' ]] || [[ $# -ne 1 ]] && [[ $# -ne 5 ]]; then
    echo $DESCRIPTION
    echo $INSTALL_USAGE
    echo $UPDATE_USAGE
    exit 1
fi

# Determine whether this will be an upgrade or fresh install:
if test -d $APPD_DIR/$MA_DIR; then
    INSTALL_TYPE="upgrade"
elif [[ $# -ne 5 ]]; then
    echo "Values for $CONTROLLER_INFO_FILE must be provided for fresh installs."
    echo $INSTALL_USAGE
    exit 1
else
    INSTALL_TYPE="fresh_install"
fi

# Determine whether the system is using Systemd or SysV Init:
DAEMON_MGR='systemd'
if ! which systemctl > /dev/null; then
    DAEMON_MGR='init'
fi &&

if ! id $APPD_USER > /dev/null 2>&1; then
    echo "Creating user: $APPD_USER"
    useradd $APPD_USER -s /usr/sbin/nologin
fi &&

if ! test -d $APPD_DIR; then
    echo "Creating directory: $APPD_DIR"
    install -o $APPD_USER -g $APPD_USER -d $APPD_DIR
fi &&

cd $APPD_DIR &&

echo "Starting $INSTALL_TYPE."

if [[ $INSTALL_TYPE == "upgrade" ]]; then
    if [[ $DAEMON_MGR == 'systemd' ]]; then
        echo "Stopping $SYSTEMD_APPD_MA_SERVICE"
        systemctl stop $SYSTEMD_APPD_MA_SERVICE
    else
        echo "Stopping $SYSV_APPD_MA_SERVICE"
        service $SYSV_APPD_MA_SERVICE stop > /dev/null
    fi
    echo "Creating backup of $MA_DIR."
    mv $MA_DIR $MA_DIR_BACKUP
fi &&

echo "Unzipping package to $APPD_DIR/$MA_DIR"
unzip $CWD/$zip_file -d $APPD_DIR/$MA_DIR > /dev/null &&
chown -R $APPD_USER:$APPD_USER $APPD_DIR/$MA_DIR &&

# Providing the controller-info arguments forces the new values for both fresh installs and upgrades.
if [[ $# -eq 5 ]]; then
    echo "Generating new $CONTROLLER_INFO_FILE"
    generateControllerInfo
else
    echo "Copying existing $CONTROLLER_INFO_FILE"
    cp $MA_DIR_BACKUP/$CONTROLLER_INFO_FILE $MA_DIR/$CONTROLLER_INFO_FILE
fi &&

# Determine where configuration like JAVA_OPTS should be set:
if [[ $DAEMON_MGR == 'systemd' ]]; then
    cd $MA_DIR/etc/systemd/system &&
    CONFIG_FILE=$SYSTEMD_APPD_MA_SERVICE
else
    cd $MA_DIR/etc/sysconfig &&
    CONFIG_FILE=$SYSV_APPD_MA_SERVICE
fi

# Determine where to insert the JAVA_OPTS:
JAVA_OPTS_LINE_NMBR=$(grep -n 'Environment="JAVA_OPTS' $CONFIG_FILE | tail -1 | awk -F: '{print $1}')
if [[ -z $JAVA_OPTS_LINE_NMBR ]]; then
    JAVA_OPTS_LINE_NMBR=12  # best guess
else
    JAVA_OPTS_LINE_NMBR=$((JAVA_OPTS_LINE_NMBR + 1))
fi &&

# Add the JAVA_OPTS
# Copy the service file to the system's service directory.
# Create a symlink for the SysV config file if it doesn't exist. 
if [[ $DAEMON_MGR == 'systemd' ]]; then
    echo "Adding the JAVA_OPTS line to the $SYSTEMD_APPD_MA_SERVICE file."
    sed -i "$JAVA_OPTS_LINE_NMBR i Environment=\"JAVA_OPTS=-Xms128m -Xmx256m\"" $SYSTEMD_APPD_MA_SERVICE &&
    echo "Copying $SYSTEMD_APPD_MA_SERVICE to $SYSTEMD_SERVICE_DIR"
    cp $SYSTEMD_APPD_MA_SERVICE $SYSTEMD_SERVICE_DIR
else
    echo "Adding the JAVA_OPTS line to the $SYSV_APPD_MA_SERVICE file."
    sed -i "$JAVA_OPTS_LINE_NMBR i JAVA_OPTS=\"-Xms128m -Xmx256m\"" $SYSV_APPD_MA_SERVICE &&
    if ! file $SYSV_APPD_SYSCONFIG | grep -q "symbolic link"; then
        echo "Creating symlink."
        ln -s $APPD_DIR/$MA_DIR/etc/sysconfig/appdynamics-machine-agent $SYSV_APPD_SYSCONFIG &&
        ls -l $SYSV_APPD_SYSCONFIG
    fi &&
    cp $APPD_DIR/$MA_DIR/etc/init.d/$SYSV_APPD_MA_SERVICE $SYSV_SERVICE_DIR
fi &&

# For SystemD systems, check the symlink to appdynamics-machine-agent.service and enable the appd service if not already.
# For SysV systems, add/enable the Appd service.  If already added/enabled, this won't hurt anything.
if [[ $DAEMON_MGR == 'systemd' ]]; then
    if ! file $SYSTEMD_SERVICE_DIR/multi-user.target.wants/$SYSTEMD_APPD_MA_SERVICE | grep -q "symbolic link"; then
        echo "Enabling $SYSTEMD_APPD_MA_SERVICE"
        systemctl enable $SYSTEMD_APPD_MA_SERVICE
    fi &&
    systemctl daemon-reload
else
    if which chkconfig > /dev/null; then
        chkconfig --add appdynamics-machine-agent > /dev/null
    else
        update-rc.d appdynamics-machine-agent defaults > /dev/null
    fi
fi &&

# Start the AppD service:
if [[ $DAEMON_MGR == 'systemd' ]]; then
    echo "Starting $SYSTEMD_APPD_MA_SERVICE"
    systemctl start $SYSTEMD_APPD_MA_SERVICE
else
    echo "Starting $SYSV_APPD_MA_SERVICE"
    service $SYSV_APPD_MA_SERVICE start > /dev/null
fi &&

echo "Removing backup."
rm -rf $APPD_DIR/$MA_DIR_BACKUP
echo "Done."
