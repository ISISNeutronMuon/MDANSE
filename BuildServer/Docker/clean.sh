# Return the docker containers that are exited
exited_containers=`docker ps -q -f "status=exited"`
# If some have been found, remove them
if [ -n "$exited_containers" ]
then
    docker rm -f ${exited_containers}
fi

# Return the docker images that are in dangling state
images=`docker images -q -f "dangling=true"`
# If some dangling images have been found, remove them
if [ -n "$images" ]
then
    docker rmi -f ${images}
fi
