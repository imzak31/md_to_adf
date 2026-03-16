class MdToAdf < Formula
  include Language::Python::Virtualenv

  desc "Convert Markdown to Atlassian Document Format (ADF) and upload to Confluence"
  homepage "https://github.com/imzak31/md-to-adf"
  url "https://files.pythonhosted.org/packages/source/m/md-to-adf/md_to_adf-1.0.1.tar.gz"
  sha256 "b862f092cd18aab76b05bbd709a6c2b3e0e9663988686e4cc566d6830b16b0e0"
  license "MIT"

  depends_on "python@3.12"

  resource "tomli_w" do
    url "https://files.pythonhosted.org/packages/source/t/tomli_w/tomli_w-1.2.0.tar.gz"
    sha256 "2dd14fac5a47c27be9cd4c976af5a12d87fb1f0b4512f81d69cce3b35ae25021"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    (testpath / "test.md").write("# Hello\n\nWorld")
    output = shell_output("#{bin}/md-to-adf convert #{testpath}/test.md")
    assert_match '"type": "doc"', output
  end
end
