
group { "puppet":
	ensure => "present",
}

# Let's update the system
exec { "update-apt":
	command => "sudo apt-get update",
    path => "/usr/bin",
}

exec {"install-docker":
	command => "/usr/bin/curl -sSL https://get.docker.io/ubuntu/ | sudo /bin/sh",
	require => Exec['update-apt'] # The system update needs to run first
}

# Let's install the dependecies
#package {
#	#["python", "python-dev", "gettext", "python-pip", "zlib1g", "zlib1g-dev", "libblas3", "libblas-dev", "liblapack3", "liblapack-dev", "gfortran", "python-numpy", "python-scipy"]:
#	["build-essential", "docker.io"]:
#	ensure => installed,
#	require => Exec['update-apt'] # The system update needs to run first
#}

#exec {"pip-install-cython":
#    command => "sudo pip install -U cython",
#    path => "/usr/bin",
#    require => Package["python", "python-dev", "gettext", "python-pip", "zlib1g", "zlib1g-dev", "libblas3", "libblas-dev", "liblapack3", "liblapack-dev", "gfortran", "python-numpy", "python-scipy"],
#}

#exec {"pip-install-gemini":
#    command => "sudo pip install gemini --allow-external python-graph-core --allow-unverified python-graph-core --allow-external python-graph-dot --allow-unverified python-graph-dot",
#    path => "/usr/bin",
#    require => Exec['pip-install-cython'],
#}

# Let's install the project dependecies from pip
#exec { "pip-install-requirements":
#    command => "sudo /usr/bin/pip install -r $PROJ_DIR/requirements.txt",
#	 path => "/usr/bin",	
#    tries => 2,
#    timeout => 600, # Too long, but this can take awhile
#    require => Exec['pip-install-gemini'], # The package dependecies needs to run first
#    logoutput => on_failure,
#}
