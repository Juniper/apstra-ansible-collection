#!/bin/bash -e
set -o pipefail

: ${TAG:="latest"}

PLATFORM=$(uname -p)
if [[ -z $PLATFORM ]]; then
  echo "PLATFORM undefined"
  exit 1
fi

# Change to script directory
cd "${0%/*}"

# Make sure credentials are set
if [[ -z "$RH_USERNAME" || -z "$RH_PASSWORD" ]]; then
  echo "Please set RH_USERNAME and RH_PASSWORD environment variables (perhaps in .env file)"
  exit 1
fi

# Function to build the Docker image
build_image() {
  docker login -u "$RH_USERNAME" -p "$RH_PASSWORD" registry.redhat.io
  ansible-builder build -t apstra-ee -f ee-builder.yml --verbosity=3 --build-arg RH_USERNAME="$RH_USERNAME" --build-arg RH_PASSWORD="$RH_PASSWORD"
}

# Function to tag the Docker image
tag_image() {
  docker tag apstra-ee:latest "$REGISTRY_URL/apstra-ee:$TAG"
}

# Function to push the Docker image
push_image() {
  docker push "$REGISTRY_URL/apstra-ee:$TAG"
  echo "Decision environment image is pushed at $REGISTRY_URL/apstra-ee:$TAG"
}

# Function to export the Docker image
export_image() {
  docker save apstra-ee:latest | gzip > apstra-ee-$PLATFORM-$TAG.image.tgz
}

if [[ -n "$REGISTRY_URL" ]]; then
  echo "Using REGISTRY_URL: $REGISTRY_URL"
else
  echo "REGISTRY_URL is not set. Tag/push will be skipped."
fi
echo "Using TAG: $TAG"

# get the collection version from TAG
collection_version=$(echo $TAG | cut -d'-' -f 1)
if [[ ! "$collecion_version" == "latest" ]]; then
  ansible_galaxy_version_arg="==$collection_version"
fi
if [[ ! -r collections/juniper-apstra.tar.gz ]]; then
  # otherwise, download the specific version
  ansible-galaxy collection download juniper.apstra${ansible_galaxy_version_arg}
  mv collections/juniper-apstra-*.tar.gz collections/juniper-apstra.tar.gz
fi

# Build the image
[[ -n $SKIP_BUILD ]] || build_image

# Export the image
export_image

# Tag and push the image if REGISTRY_URL is set
if [[  -n "$REGISTRY_URL" ]] && [[ -z $SKIP_BUILD ]]; then
  # Tag the image
  tag_image

  # Push the image
  push_image
else
  echo "Skipping pushing the image to registry"
fi
