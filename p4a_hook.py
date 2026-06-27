"""Increase Gradle heap for large APKs (OCR ONNX models + dual-arch native libs)."""

from os.path import join

JVMARGS = (
    "org.gradle.jvmargs=-Xmx6144m -XX:MaxMetaspaceSize=1024m "
    "-XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8\n"
)


def _ensure_jvmargs(dist_dir):
    path = join(dist_dir, "gradle.properties")
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except FileNotFoundError:
        return
    if "org.gradle.jvmargs" in text:
        return
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text.rstrip() + "\n" + JVMARGS)


def before_apk_assemble(buildozer):
    _ensure_jvmargs(buildozer._dist.dist_dir)
