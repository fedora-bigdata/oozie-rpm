%global hadoop_version 2.2.0
%global pig_version 0.12.0
%global java_version 1.8
%global target_java_version 1.7

%global commit fe8d85a4f0467f3ad7e8d7fc8ab4ebd89fa5fe3f
%global shortcommit %(c=%{commit}; echo ${c:0:7})

%bcond_with javadoc

Name: oozie
Version: 4.0.1
Release: 1%{?dist}
Summary: A work-flow scheduling system for Apache Hadoop
License: ASL 2.0
URL: http://oozie.apache.org
Source0: https://github.com/apache/%{name}/archive/%{commit}/%{name}-%{version}-%{shortcommit}.tar.gz
Source1: %{name}.sysconfig
Source2: %{name}-tomcat-users.xml
Source3: %{name}-site.xml
Source4: %{name}-env.sh
Source5: %{name}-hive.xml
Source6: %{name}
Source7: %{name}db.sh
Source8: %{name}.logrotate
Patch0: %{name}-jetty8.patch
Patch1: %{name}-no-download-tomcat.patch
Patch2: %{name}-assemblies.patch
Patch3: %{name}-commons-collections4.patch
# Modified version of patch to apply for this oozie version
# https://issues.apache.org/jira/browse/OOZIE-1440
Patch4: %{name}-xerces.patch
ExcludeArch: %{arm}
BuildArch: noarch

BuildRequires: apache-commons-collections4
BuildRequires: apache-log4j-extras
BuildRequires: antlr3-java
BuildRequires: ehcache-core
BuildRequires: hadoop-client
BuildRequires: hadoop-common
BuildRequires: hadoop-hdfs
BuildRequires: hadoop-mapreduce
BuildRequires: hadoop-tests
BuildRequires: hadoop-yarn
BuildRequires: hbase
BuildRequires: hive
BuildRequires: hive-hcatalog
BuildRequires: java-devel
BuildRequires: json_simple
BuildRequires: jung
BuildRequires: jython
BuildRequires: maven-checkstyle-plugin
BuildRequires: maven-dependency-plugin
BuildRequires: maven-local
BuildRequires: maven-war-plugin
BuildRequires: openjpa-tools
BuildRequires: pig
BuildRequires: postgresql-jdbc
BuildRequires: tomcat
BuildRequires: tomcat-log4j

Requires: java-headless
Requires: tomcat

%description
Apache Oozie is an extensible, scalable and reliable system to define,
manage, schedule, and execute complex Apache Hadoop workloads via
web services

%if %{with javadoc}
%package javadoc
Summary: Javadoc for %{name}

%description javadoc
This package contains the API documentation for %{name}.
%endif

%prep
%setup -qn %{name}-%{commit}
%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1

# Disable sqoop module because sqoop is missing
%pom_disable_module sqoop sharelib
%pom_remove_dep org.apache.%{name}:%{name}-sharelib-sqoop webapp

# Remove the maven-findbugs plugin
%pom_remove_plugin :findbugs-maven-plugin

# Remove the maven-clover2-plugin plugin
%pom_remove_plugin :maven-clover2-plugin

# Disable or remove the maven-assembly-plugin in poms that access an empty
# assembly configuration file
%pom_xpath_remove "pom:project/pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-assembly-plugin']/pom:configuration/pom:descriptors"
%pom_xpath_inject "pom:project/pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-assembly-plugin']/pom:configuration" "
<skipAssembly>true</skipAssembly>
"

# Because the high level pom accesses an empty assembly configuration which
# had to be disabled, enable the plugin on projects using actual assembly
# configurations
for p in client distro docs examples hadooplibs/hadoop-2 \
         hadooplibs hbaselibs/hbase-0.94 hbaselibs hcataloglibs/hcatalog-0.5 \           hcataloglibs sharelib/distcp sharelib/hcatalog sharelib/hive \
         sharelib/oozie sharelib/pig sharelib sharelib/streaming tools
do
  %pom_xpath_inject "pom:project/pom:build/pom:plugins/pom:plugin[pom:artifactId='maven-assembly-plugin']/pom:configuration" "
<skipAssembly>false</skipAssembly>
" $p
done

# Fix the hsqldb coordinates
%pom_xpath_set "pom:project/pom:dependencyManagement/pom:dependencies/pom:dependency[pom:artifactId='hsqldb']/pom:groupId" "org.hsqldb"
%pom_xpath_set "pom:project/pom:dependencies/pom:dependency[pom:artifactId='hsqldb']/pom:groupId" "org.hsqldb" core
%pom_xpath_set "pom:project/pom:dependencies/pom:dependency[pom:artifactId='hsqldb']/pom:groupId" "org.hsqldb" examples

# Fix log4j version
%pom_xpath_set "pom:project/pom:dependencyManagement/pom:dependencies/pom:dependency[pom:artifactId='log4j']/pom:version" "1.2.17"

# Remove test build dependencies because of missing test dependency greenmail
%pom_remove_dep com.icegreen:greenmail core

%pom_remove_dep org.apache.activemq:activemq-broker
%pom_remove_dep org.apache.activemq:activemq-kahadb-store 
%pom_remove_dep org.apache.activemq:activemq-broker core
%pom_remove_dep org.apache.activemq:activemq-kahadb-store core

%pom_xpath_remove "pom:project/pom:dependencies/pom:dependency[pom:artifactId='%{name}-core' and pom:classifier='tests']" examples
%pom_xpath_remove "pom:project/pom:dependencies/pom:dependency[pom:artifactId='%{name}-core' and pom:type='test-jar']" minitest
%pom_xpath_remove "pom:project/pom:dependencies/pom:dependency[pom:artifactId='%{name}-core' and pom:classifier='tests']" sharelib/distcp
%pom_xpath_remove "pom:project/pom:dependencies/pom:dependency[pom:artifactId='%{name}-core' and pom:classifier='tests']" sharelib/hive
%pom_xpath_remove "pom:project/pom:dependencies/pom:dependency[pom:artifactId='%{name}-core' and pom:classifier='tests']" sharelib/pig
%pom_xpath_remove "pom:project/pom:dependencies/pom:dependency[pom:artifactId='%{name}-core' and pom:classifier='tests']" sharelib/streaming
%pom_xpath_remove "pom:project/pom:dependencies/pom:dependency[pom:artifactId='%{name}-core' and pom:classifier='tests']" tools

# Remove this openjpa dependency.  It's not needed and is invalid with
# current version of openjpa
%pom_xpath_remove "pom:project/pom:build/pom:plugins/pom:plugin[pom:artifactId='openjpa-maven-plugin']/pom:dependencies/pom:dependency[pom:artifactId='openjpa']" core

# Change the json import to use json-simple
sed -i "s/json.JSONObject/json.simple.JSONObject/" core/src/main/java/org/apache/%{name}/util/ELConstantsFunctions.java

# Change to use geronimo-jms instead of activemq-client
%pom_remove_dep org.apache.activemq:activemq-client
%pom_remove_dep org.apache.activemq:activemq-client client
%pom_add_dep org.apache.geronimo.specs:geronimo-jms_1.1_spec 
%pom_add_dep org.apache.geronimo.specs:geronimo-jms_1.1_spec client

# Disable building against other hadoop versions
%pom_disable_module hadoop-1 hadooplibs
%pom_disable_module hadoop-distcp-1 hadooplibs
%pom_disable_module hadoop-test-1 hadooplibs
%pom_disable_module hadoop-0.23 hadooplibs
%pom_disable_module hadoop-distcp-0.23 hadooplibs
%pom_disable_module hadoop-test-0.23 hadooplibs

# Correct the hbase dependency and update to newer version
%pom_xpath_set "pom:project/pom:dependencies/pom:dependency[pom:groupId='org.apache.hbase']/pom:artifactId" "hbase-common" hbaselibs/hbase-0.94

# Correct hcatalog dependency and update to newer version
%pom_disable_module hcatalog-0.6 hcataloglibs
%pom_xpath_set "pom:project/pom:dependencies/pom:dependency[pom:artifactId='hcatalog-server-extensions']/pom:groupId" "org.apache.hive.hcatalog" hcataloglibs/hcatalog-0.5
%pom_xpath_set "pom:project/pom:dependencies/pom:dependency[pom:artifactId='hcatalog-core']/pom:groupId" "org.apache.hive.hcatalog" hcataloglibs/hcatalog-0.5
%pom_xpath_set "pom:project/pom:dependencies/pom:dependency[pom:artifactId='hcatalog-pig-adapter']/pom:groupId" "org.apache.hive.hcatalog" hcataloglibs/hcatalog-0.5
%pom_xpath_set "pom:project/pom:dependencies/pom:dependency[pom:artifactId='webhcat-java-client']/pom:groupId" "org.apache.hive.hcatalog" hcataloglibs/hcatalog-0.5
%pom_xpath_set "pom:project/pom:dependencies/pom:dependency[pom:artifactId='%{name}-hcatalog']/pom:exclusions/pom:exclusion[pom:artifactId='hcatalog-server-extensions']/pom:groupId" "org.apache.hive.hcatalog" sharelib/hcatalog

# Remove obsoleted/unpackaged hive deps
%pom_remove_dep org.apache.hive:hive-contrib sharelib/hive
%pom_remove_dep org.apache.hive:hive-builtins sharelib/hive

# Remove the deps on webapp war
%pom_xpath_remove "pom:project/pom:dependencyManagement/pom:dependencies/pom:dependency[pom:artifactId='%{name}-webapp' and pom:type='war']"
%pom_xpath_remove "pom:project/pom:dependencies/pom:dependency[pom:artifactId='%{name}-webapp' and pom:type='war']" distro

# Remove the deps on docs war
%pom_xpath_remove "pom:project/pom:dependencyManagement/pom:dependencies/pom:dependency[pom:artifactId='%{name}-docs' and pom:type='war']" 
%pom_remove_dep :oozie-docs webapp

# Files we don't want
%mvn_package :%{name}-docs __noinstall
%mvn_package :%{name}*-test __noinstall
%mvn_package :%{name}*:war: __noinstall
%mvn_package :%{name}*:tar.gz: __noinstall

%build
%if %{without javadoc}
args="-j"
%endif
%mvn_build $args -- -DjavaVersion=%{java_version} -DtargetJavaVersion=%{target_java_version} -Phadoop-2 -DskipTests -Dmaven.test.skip=true -Dpig.version=%{pig_version} -Dpig.classifier="" package assembly:single

%install
# Replace oozie jars with symlinks
# $1 the src directory
link_oozie_jars()
{
  pushd $1
    for f in `ls %{name}-*`
    do
      n=`echo $f | sed "s/-%{version}//"`
      n=`echo $n | sed "s/-%{hadoop_version}.%{name}//"`
      rm -f $f
      p=`find %{buildroot}/%{_javadir}/%{name} -name $n | sed "s|%{buildroot}||"`
      %{__ln_s} $p $f
    done
  popd
}

%mvn_install

install -d -m 0755 %{buildroot}/%{_bindir}
install -d -m 0755 %{buildroot}/%{_datadir}/%{name}/%{name}-server/webapps/%{name}
install -d -m 0755 %{buildroot}/%{_datadir}/%{name}/bin
install -d -m 0755 %{buildroot}/%{_datadir}/%{name}/lib
install -d -m 0755 %{buildroot}/%{_datadir}/%{name}/libtools
install -d -m 0755 %{buildroot}/%{_sbindir}
install -d -m 0755 %{buildroot}/%{_sharedstatedir}/tomcats/%{name}
install -d -m 0755 %{buildroot}/%{_sysconfdir}/%{name}/action-conf
install -d -m 0755 %{buildroot}/%{_sysconfdir}/%{name}/tomcat/Catalina/localhost
install -d -m 0755 %{buildroot}/%{_sysconfdir}/logrotate.d
install -d -m 0755 %{buildroot}/%{_sysconfdir}/sysconfig
install -d -m 0755 %{buildroot}/%{_var}/cache/%{name}/data
install -d -m 0755 %{buildroot}/%{_var}/cache/%{name}/temp
install -d -m 0755 %{buildroot}/%{_var}/cache/%{name}/work
install -d -m 0755 %{buildroot}/%{_var}/log/%{name}

pushd %{buildroot}/%{_sharedstatedir}/tomcats/%{name}
  %{__ln_s} %{_datadir}/%{name}/%{name}-server/conf conf
  %{__ln_s} %{_datadir}/%{name}/%{name}-server/lib lib
  %{__ln_s} %{_datadir}/%{name}/%{name}-server/logs logs
  %{__ln_s} %{_datadir}/%{name}/%{name}-server/temp temp
  %{__ln_s} %{_datadir}/%{name}/%{name}-server/webapps webapps
  %{__ln_s} %{_datadir}/%{name}/%{name}-server/work work
popd

# Copy the tomcat configuration and overlay with specific configuration bits.
# This is needed so the httpfs instance won't collide with a system running
# tomcat
for f in catalina.policy catalina.properties context.xml log4j.properties \
         tomcat.conf web.xml;
do
  cp -a %{_sysconfdir}/tomcat/$f %{buildroot}/%{_sysconfdir}/%{name}/tomcat
done

install -m 660 %{SOURCE2} %{buildroot}/%{_sysconfdir}/%{name}/tomcat/tomcat-users.xml
install -m 664 distro/src/main/tomcat/*.* %{buildroot}/%{_sysconfdir}/%{name}/tomcat
sed -i "/ServerLifecycleListener/d" %{buildroot}/%{_sysconfdir}/%{name}/tomcat/server.xml
sed -i "/ServerLifecycleListener/d" %{buildroot}/%{_sysconfdir}/%{name}/tomcat/ssl-server.xml

pushd %{buildroot}/%{_datadir}/%{name}/%{name}-server
  %{__ln_s} %{_datadir}/tomcat/bin bin
  %{__ln_s} %{_sysconfdir}/%{name}/tomcat conf
  %{__ln_s} %{_datadir}/tomcat/lib lib
  %{__ln_s} %{_var}/cache/%{name}/temp temp
  %{__ln_s} %{_var}/cache/%{name}/work work
  %{__ln_s} %{_var}/log/%{name} logs
popd

pushd %{buildroot}/%{_datadir}/%{name}
  %{__ln_s} %{_sysconfdir}/%{name} conf
  %{__ln_s} %{_var}/cache/%{name}/data data
  %{__ln_s} %{_var}/log/%{name} logs
popd

# Copy the webapp
cp -arf webapp/target/%{name}-webapp-%{version}/* %{buildroot}/%{_datadir}/%{name}/%{name}-server/webapps/%{name}

# Tell tomcat to follow symlinks
sed -i "s|\(path=.*\)>|\1 allowLinking=\"true\">|" %{buildroot}/%{_datadir}/%{name}/%{name}-server/webapps/%{name}/META-INF/context.xml

# Remove the jars included in the webapp and create symlinks
rm -f %{buildroot}/%{_datadir}/%{name}/%{name}-server/webapps/%{name}/WEB-INF/lib/javax.servlet-*
%{_bindir}/xmvn-subst %{buildroot}/%{_datadir}/%{name}/%{name}-server/webapps/%{name}/WEB-INF/lib
link_oozie_jars %{buildroot}/%{_datadir}/%{name}/%{name}-server/webapps/%{name}/WEB-INF/lib

pushd %{buildroot}/%{_datadir}/%{name}/%{name}-server/webapps/%{name}/WEB-INF/lib
  # Link in bits from hadoop
  build-jar-repository . hadoop/hadoop-common \
    hadoop/hadoop-mapreduce-client-core hadoop/hadoop-mapreduce-client-common \
    hadoop/hadoop-mapreduce-client-jobclient hadoop/hadoop-mapreduce-client-app \
    hadoop/hadoop-yarn-common hadoop/hadoop-yarn-api hadoop/hadoop-hdfs \
    hadoop/hadoop-auth

  # Link in hadoop jar deps
  build-jar-repository . protobuf commons-configuration commons-cli commons-io
popd

# Copy support libs and create symlinks
pushd distro/target/%{name}-%{version}-distro/%{name}-%{version}
  cp -af lib/* %{buildroot}/%{_datadir}/%{name}/lib
  cp -af libtools/* %{buildroot}/%{_datadir}/%{name}/libtools
  rm -f %{buildroot}/%{_datadir}/%{name}/libtools/tools-*
  xmvn-subst %{buildroot}/%{_datadir}/%{name}/lib
  xmvn-subst %{buildroot}/%{_datadir}/%{name}/libtools
  link_oozie_jars %{buildroot}/%{_datadir}/%{name}/lib
  link_oozie_jars %{buildroot}/%{_datadir}/%{name}/libtools
popd

# Copy configuration
pushd distro/target/%{name}-%{version}-distro/%{name}-%{version}/conf
  install -m 0644 adminusers.txt %{buildroot}/%{_sysconfdir}/%{name}
  install -m 0644 oozie-log4j.properties %{buildroot}/%{_sysconfdir}/%{name}
popd
install -m 0644 %{SOURCE3} %{buildroot}/%{_sysconfdir}/%{name}
install -m 0644 %{SOURCE4} %{buildroot}/%{_sysconfdir}/%{name}
install -m 0644 %{SOURCE5} %{buildroot}/%{_sysconfdir}/%{name}/action-conf

# Copy scripts
cp -arf distro/target/%{name}-%{version}-distro/%{name}-%{version}/bin/* %{buildroot}/%{_datadir}/%{name}/bin
install -m 0755 %{SOURCE6} %{buildroot}/%{_bindir}
install -m 0755 %{SOURCE7} %{buildroot}/%{_bindir}

install -m 0644 %{SOURCE1} %{buildroot}/%{_sysconfdir}/sysconfig/tomcat@%{name}

# logrotate config
install -m 0644 %{SOURCE8} %{buildroot}/%{_sysconfdir}/logrotate.d/%{name}

%files -f .mfiles
%doc LICENSE.txt NOTICE.txt README.txt
%dir %{_javadir}/%{name}
%dir %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/adminusers.txt
%config(noreplace) %{_sysconfdir}/%{name}/oozie-site.xml
%config(noreplace) %{_sysconfdir}/%{name}/oozie-log4j.properties
%config(noreplace) %{_sysconfdir}/%{name}/oozie-env.sh
%config(noreplace) %{_sysconfdir}/%{name}/action-conf
%attr(-,tomcat,tomcat) %config(noreplace) %{_sysconfdir}/%{name}/tomcat/*.*
%attr(0775,root,tomcat) %dir %{_sysconfdir}/%{name}/tomcat
%attr(0775,root,tomcat) %dir %{_sysconfdir}/%{name}/tomcat/Catalina
%attr(0775,root,tomcat) %dir %{_sysconfdir}/%{name}/tomcat/Catalina/localhost
%config(noreplace) %{_sysconfdir}/sysconfig/tomcat@%{name}
%{_bindir}/*
%{_datadir}/%{name}
%{_sharedstatedir}/tomcats/%{name}
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%attr(0775,root,tomcat) %dir %{_var}/log/%{name}
%attr(0775,root,tomcat) %dir %{_var}/cache/%{name}
%attr(0775,root,tomcat) %dir %{_var}/cache/%{name}/data
%attr(0775,root,tomcat) %dir %{_var}/cache/%{name}/temp
%attr(0775,root,tomcat) %dir %{_var}/cache/%{name}/work

%if %{with javadoc}
%files -f .mfiles-javadoc javadoc
%doc LICENSE.txt NOTICE.txt 
%endif

%changelog
* Fri Feb 28 2014 Robert Rati <rrati@redhat> - 4.0.0-1
- Initial packaging
