import libvirt
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
import virtinst.util as util
from webvirtmgr.model.models import *


def index(request, host_id, vname):

   if not request.user.is_authenticated():
      return HttpResponseRedirect('/')

   kvm_host = Host.objects.get(user=request.user.id, id=host_id)

   def add_error(msg, type_err):
      error_msg = Log(host_id=host_id, 
                     type=type_err, 
                     message=msg, 
                     user_id=request.user.id
                     )
      error_msg.save()

   if not kvm_host.login or not kvm_host.passwd:
      def creds(credentials, user_data):
         for credential in credentials:
            if credential[0] == libvirt.VIR_CRED_AUTHNAME:
               credential[4] = request.session['login_kvm']
               if len(credential[4]) == 0:
                  credential[4] = credential[3]
            elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
               credential[4] = request.session['passwd_kvm']
            else:
               return -1
         return 0
   else:
      def creds(credentials, user_data):
         for credential in credentials:
            if credential[0] == libvirt.VIR_CRED_AUTHNAME:
               credential[4] = kvm_host.login
               if len(credential[4]) == 0:
                  credential[4] = credential[3]
            elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
               credential[4] = kvm_host.passwd
            else:
               return -1
         return 0

   def vm_conn():
      flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
      auth = [flags, creds, None]
      uri = 'qemu+tcp://' + kvm_host.ipaddr + '/system'
      try:
         conn = libvirt.openAuth(uri, auth, 0)
         return conn
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_dom(vname):
      try:
         dom = conn.lookupByName(vname)
         return dom
      except:
         print "Not connected"

   def get_vm_vnc():
      try:
         xml = dom.XMLDesc(0)
         vnc = util.get_xml_path(xml, "/domain/devices/graphics/@port")
         return vnc
      except:
         print "Get vnc port failed"

   conn = vm_conn()
   dom = get_dom(vname)

   if conn == None:
      return HttpResponseRedirect('/overview/%s/' % (host_id))

   vnc_port = get_vm_vnc()
   
   if kvm_host.passwd:
      vnc_auth = 'S0vd0d' + kvm_host.passwd + 'p4yU9'
   else:
      vnc_auth = 'S0vd0d' + request.session['passwd_kvm'] + 'p4yU9'

   print vnc_auth

   conn.close()

   return render_to_response('vnc.html', locals())

def redir_two(request, host_id):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/user/login/')
   else:
      return HttpResponseRedirect('/dashboard/')

def redir_one(request):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/user/login/')
   else:
      return HttpResponseRedirect('/')
