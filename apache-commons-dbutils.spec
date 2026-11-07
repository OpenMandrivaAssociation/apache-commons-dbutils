Name:		apache-commons-dbutils
Version:	1.8.1
Release:	1
Summary:	JDBC helper classes
Group:		Development/Java
License:	ASL 2.0
URL:		https://commons.apache.org/proper/commons-dbutils/
Source0:	https://github.com/apache/commons-dbutils/archive/refs/tags/rel/commons-dbutils-%{version}.tar.gz#/commons-dbutils-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	python
BuildRequires:	mvn(org.apache.commons:commons-parent:pom::)
BuildRequires:	mvn(org.apache:apache:pom::)
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven
BuildOption(install):	--file-name commons-dbutils --link %{name}

%description
Apache Commons DbUtils is a thin wrapper around JDBC. 1.8.0 adds a
Column annotation and BasicRowProcessor.createCaseInsensitiveHashMap.
1.8.1 needs Java 8. Tests are skipped. The automatic module name is
org.apache.commons.dbutils.

%prep
%autosetup -n commons-dbutils-rel-commons-dbutils-%{version}
# Test dependencies are not packaged. Jacoco is bound to the test phase.
# The parent japicmp and jacoco profiles activate from marker files.
python - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path

for marker in (
    "src/site/resources/profile.jacoco",
    "src/site/resources/profile.japicmp",
):
    Path(marker).unlink()

ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

def local(tag):
    return tag.rsplit("}", 1)[-1]

path = Path("pom.xml")
tree = ET.parse(path)
root = tree.getroot()
removed = []
for parent in list(root.iter()):
    if local(parent.tag) != "dependencies":
        continue
    for child in list(parent):
        if local(child.tag) != "dependency":
            continue
        scope = artifact = ""
        for item in child:
            name = local(item.tag)
            if name == "scope":
                scope = (item.text or "").strip()
            elif name == "artifactId":
                artifact = (item.text or "").strip()
        if scope == "test":
            parent.remove(child)
            removed.append(artifact)
expected = {"junit-vintage-engine", "mockito-core", "hamcrest-all"}
if set(removed) != expected:
    raise SystemExit("unexpected dependency edit: " + " ".join(sorted(removed)))
removed_jacoco = 0
for parent in list(root.iter()):
    for child in list(parent):
        if local(child.tag) != "plugin":
            continue
        artifact = ""
        for item in child:
            if local(item.tag) == "artifactId":
                artifact = (item.text or "").strip()
        if artifact == "jacoco-maven-plugin":
            parent.remove(child)
            removed_jacoco += 1
removed_reporting = 0
for child in list(root):
    if local(child.tag) == "reporting":
        root.remove(child)
        removed_reporting += 1
if removed_jacoco != 1 or removed_reporting != 1:
    raise SystemExit(f"plugin edit failed jacoco={removed_jacoco} reporting={removed_reporting}")
tree.write(path, encoding="UTF-8", xml_declaration=True)
text = path.read_text(encoding="utf-8")
for needle in ("<scope>test</scope>", "jacoco-maven-plugin", "<reporting>", "mockito"):
    if needle in text:
        raise SystemExit("pom still contains " + needle)
if "<maven.compiler.source>1.8</maven.compiler.source>" not in text:
    raise SystemExit("compiler source missing")
PY

%build -a
cat > manifest-addition <<'EOF'
Automatic-Module-Name: org.apache.commons.dbutils
EOF
jar ufm target/commons-dbutils-%{version}.jar manifest-addition
java --module-path target/commons-dbutils-%{version}.jar --describe-module org.apache.commons.dbutils | grep -q '^org.apache.commons.dbutils'

%files -f .mfiles
%doc LICENSE.txt NOTICE.txt RELEASE-NOTES.txt README.md
