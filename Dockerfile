FROM ubuntu:18.04
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN apt-get update && apt-get install -y apt-transport-https python3.6 python3-pip git jq curl wget tar socat
RUN curl -fsSL https://clis.cloud.ibm.com/install/linux | sh
RUN wget https://github.com/openshift/origin/releases/download/v3.9.0/openshift-origin-client-tools-v3.9.0-191fece-linux-64bit.tar.gz
RUN tar -zvxf openshift-origin-client-tools-v3.9.0-191fece-linux-64bit.tar.gz > /dev/null
RUN cp openshift-origin-client-tools-v3.9.0-191fece-linux-64bit/oc /usr/local/bin/
RUN ibmcloud plugin install kubernetes-service -f
RUN ibmcloud config --check-version=false
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/`curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt`/bin/linux/amd64/kubectl
RUN chmod +x ./kubectl
RUN mv ./kubectl /usr/local/bin/kubectl
COPY files/node-inspect-template.yaml /app/node-inspect-template.yaml
COPY files/permitRootLogin.sh /app/permitRootLogin.sh
RUN chmod +x /app/permitRootLogin.sh
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt
EXPOSE 8087
ENV FLASK_APP=enable-node-ssh-02cn.py
CMD ["flask", "shell"]
