# Homebrew formula for kickback.
#
# Tap install (after you push this to github.com/gabeperez/homebrew-kickback):
#   brew install gabeperez/kickback/kickback
#
# `url`/`sha256` point at a GitHub release tarball produced by ./release.sh.
class Kickback < Formula
  desc "Kickbacks CLI — terminal companion for the Kickbacks.ai editor extension"
  homepage "https://gabeperez.github.io/kickback-cli"
  url "https://github.com/gabeperez/kickback-cli/archive/refs/tags/v0.1.1.tar.gz"
  sha256 "74f227a50d75301a0ad37324fcc7b307af0b6430908f4232cd66f16360a76be7"
  license "MIT"
  version "0.1.1"

  depends_on "python@3.12" => :recommended  # uses stdlib + openssl; cryptography optional
  depends_on :macos

  def install
    bin.install "kickback"
  end

  def caveats
    <<~EOS
      kickback is safe by default — every feature that writes anything
      (sampler, notifications, token refresh) is OFF until you enable it.

      First run:   kickback init      (writes ~/.config/kickback/config.json)
      Learn more:  kickback about     (what it reads/sends + what could break)
      Live check:  kickback doctor
    EOS
  end

  test do
    assert_match "kickback #{version}", shell_output("#{bin}/kickback --version")
  end
end
