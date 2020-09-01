#!/bin/bash
# set -x

# Git repo cloned at $WORKING_DIR, copy into $ARCHIVE_DIR
mkdir -p $ARCHIVE_DIR
cp -R -n ./ $ARCHIVE_DIR/ || true

# Record git info
echo "GIT_URL=${GIT_URL}" >> $ARCHIVE_DIR/build.properties
echo "GIT_BRANCH=${GIT_BRANCH}" >> $ARCHIVE_DIR/build.properties
echo "GIT_COMMIT=${GIT_COMMIT}" >> $ARCHIVE_DIR/build.properties
echo "SOURCE_BUILD_NUMBER=${BUILD_NUMBER}" >> $ARCHIVE_DIR/build.properties
cat $ARCHIVE_DIR/build.properties

# check if doi is integrated in this toolchain
if jq -e '.services[] | select(.service_id=="draservicebroker")' _toolchain.json; then
  # Record build information
  ibmcloud login --apikey ${IBM_CLOUD_API_KEY} --no-region
  ibmcloud doi publishbuildrecord --branch ${GIT_BRANCH} --repositoryurl ${GIT_URL} --commitid ${GIT_COMMIT} \
    --buildnumber ${BUILD_NUMBER} --logicalappname ${IMAGE_NAME} --status pass
fi

