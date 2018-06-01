# Return the docker containers that are exited
exited_containers=`docker ps -q -f "status=exited"`

# If some have been found, remove them
if [ -n "$exited_containers" ]
then
    docker rm -f ${exited_containers}
fi

# Return the docker images corresponding to MDANSE
images=`docker images -a --format "{{.Repository}}:{{.Tag}}" | grep _mdanse_` 

# If some have been found, remove them
if [ -n "$images" ]
then
    docker rmi -f ${images}
fi

